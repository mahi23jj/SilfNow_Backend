from typing import List, Dict, Tuple
from sqlmodel import Session, select

from app.models.edge import Edge
from app.repository.report_repo import get_edge_status_snapshot
from app.services.path_generatio_service import bfs_paths, build_graph
from app.schemas.route import PathRequest, EdgeExplanation, Label


MAX_ROUTES = 5
MIN_ROUTES = 3
MAX_EDGE_WAIT_TIME = 30.0
MIN_EDGE_CONFIDENCE = 0.25
MIN_ROUTE_CONFIDENCE = 0.35
MAX_SWITCHES = 3


def _normalize_status_value(status, key, default=None):
    value = status.get(key, default)
    if hasattr(value, "value"):
        return value.value
    if hasattr(value, "name"):
        return value.name
    return value


def _queue_penalty(queue_level) -> float:
    return {"LOW": 0.0, "MEDIUM": 1.0, "HIGH": 2.0}.get(str(queue_level).upper(), 1.0)


def _availability_penalty(vehicle_availability) -> float:
    availability = str(vehicle_availability).upper()
    if availability in {"UNAVAILABLE", "NONE"}:
        return 100.0
    if availability in {"LIMITED", "LOW"}:
        return 2.5
    return 0.0


def _switch_count(explanation: List[Dict]) -> int:
    switches = 0
    previous_mode = None

    for item in explanation:
        mode = item.get("mode")
        if not mode or mode == "unknown":
            continue
        if previous_mode is not None and mode != previous_mode:
            switches += 1
        previous_mode = mode

    return switches


def build_edge_lookup(session: Session) -> Dict[Tuple[str, str], Edge]:
    edges = session.exec(select(Edge)).all()

    edge_lookup: Dict[Tuple[str, str], Edge] = {}

    for e in edges:
        key = (e.from_node_id, e.to_node_id)
        edge_lookup[key] = e

    return edge_lookup



def score_transport_option(status):
    if not status:
        return -float("inf")

    vehicle_avail = _normalize_status_value(status, "vehicle_availability")
    if str(vehicle_avail).upper() in {"UNAVAILABLE", "NONE"}:
        return -float("inf")

    confidence = float(status.get("confidence") or 0)
    if confidence < MIN_EDGE_CONFIDENCE:
        return -float("inf")

    wait = float(status.get("estimated_wait_time") or 0)
    queue_level = _normalize_status_value(status, "queue_level")
    queue_penalty = _queue_penalty(queue_level)
    availability_penalty = _availability_penalty(vehicle_avail)
    num_reports = int(status.get("num_reports") or 0)
    report_bonus = min(num_reports, 10) * 0.1

    stability = str(_normalize_status_value(status, "stability", "MODERATE") or "MODERATE").upper()
    stability_penalty = 2 if stability == "UNSTABLE" else 0

    score = (
        -(wait * 1.2)
        - (queue_penalty * 1.5)
        - stability_penalty
        - availability_penalty
        + (confidence * 4)
        + report_bonus
    )

    return score


def choose_best_mode(statuses):
    best_mode = None
    best_score = -float("inf")
    best_status = None

    for s in statuses:
        score = score_transport_option(s)

        if score > best_score:
            best_score = score
            best_mode = s["transport_type"]
            best_status = s

    return best_mode, best_status



def evaluate_path(path, edge_lookup, session: Session):
    # kept for backward compatibility; real evaluation uses cached snapshots
    return evaluate_path_cached(path, edge_lookup, {}, session)


def evaluate_path_cached(path, edge_lookup, snapshot_cache: Dict, session: Session):
    total_time = 0.0
    total_cost = 0.0
    total_risk = 0.0
    explanation: List[Dict] = []

    for i in range(len(path) - 1):
        edge = edge_lookup.get((path[i], path[i+1]))

        if not edge:
            continue

        # use cached snapshot if available
        snapshot = snapshot_cache.get(str(edge.id))
        if snapshot is None:
            snapshot = get_edge_status_snapshot(edge.id, session)
            snapshot_cache[str(edge.id)] = snapshot

        statuses = snapshot.get("statuses", [])

        mode, status = choose_best_mode(statuses)

        if not status or not mode:
            # penalize missing status
            note = "no_available_transport"
            fallback_time = float(edge.base_travel_time_min or 5)
            total_time += fallback_time
            total_cost += (edge.base_cost_max or 5)
            total_risk += 2.5
            explanation.append({
                "edge": f"{path[i]}->{path[i+1]}",
                "mode": "unknown",
                "time": fallback_time,
                "wait_time": fallback_time,
                "cost": edge.base_cost_max or 5,
                "risk": 2.5,
                "confidence": 0.0,
                "queue_level": None,
                "vehicle_availability": None,
                "num_reports": 0,
                "stability": None,
                "note": note,
            })
            continue

        # normalize values
        est_wait = float(status.get("estimated_wait_time") or 0)
        queue_level = _normalize_status_value(status, "queue_level", "MEDIUM")
        vehicle_availability = _normalize_status_value(status, "vehicle_availability", "AVAILABLE")
        stability = str(_normalize_status_value(status, "stability", "MODERATE") or "MODERATE").upper()
        confidence = float(status.get("confidence") or 0)
        num_reports = int(status.get("num_reports") or 0)

        queue_penalty = _queue_penalty(queue_level)
        availability_penalty = _availability_penalty(vehicle_availability)
        report_penalty = max(0.0, 5 - min(num_reports, 5)) * 0.2
        stability_penalty = 1.0 if stability == "UNSTABLE" else 0.0

        # ---- TIME ----
        base_travel = float(edge.base_travel_time_min or 0)
        if str(mode).lower() == "taxi":
            base_travel = float(edge.base_travel_time_max or base_travel)

        edge_time = base_travel + est_wait + (queue_penalty * 1.5) + availability_penalty
        total_time += edge_time

        # ---- COST ----
        if str(mode).lower() == "bus":
            edge_cost = float(edge.base_cost_min or 0)
        else:
            edge_cost = float(edge.base_cost_max or 0)

        total_cost += edge_cost

        # ---- RISK ----
        risk = ((1.0 - confidence) * 2.0) + (queue_penalty * 0.5) + availability_penalty + report_penalty + stability_penalty

        total_risk += risk

        explanation.append({
            "edge": f"{path[i]}->{path[i+1]}",
            "mode": mode,
            "time": edge_time,
            "wait_time": est_wait,
            "cost": edge_cost,
            "risk": risk,
            "confidence": confidence,
            "queue_level": queue_level,
            "vehicle_availability": vehicle_availability,
            "num_reports": num_reports,
            "stability": stability,
            "note": None,
        })

    return total_time, total_cost, total_risk, explanation


def compute_final_score(time, cost, risk, preference: str):
    # all scores are negative for easier max selection semantics
    if preference == "fastest":
        return -(time * 1.0 + risk * 2.0 + cost * 0.2)

    if preference == "cheapest":
        return -(cost * 1.5 + time * 0.5 + risk * 1.0)

    if preference == "reliable":
        return -(risk * 3.0 + time * 0.5 + cost * 0.2)

    # balanced
    return -(time * 1.0 + cost * 0.8 + risk * 1.5)


def _route_has_valid_edges(explanation: List[Dict]) -> bool:
    if not explanation:
        return False

    for item in explanation:
        if item.get("note") == "no_available_transport":
            return False
        if float(item.get("wait_time") or 0) > MAX_EDGE_WAIT_TIME:
            return False
        if float(item.get("confidence") or 0) < MIN_EDGE_CONFIDENCE:
            return False

    return True


def _build_route_summary(path: List, time: float, cost: float, risk: float, explanation: List[Dict], preference: str) -> Dict:
    switch_count = _switch_count(explanation)
    adjusted_score = compute_final_score(time, cost, risk, preference) - (switch_count * 0.35)

    if switch_count > MAX_SWITCHES:
        adjusted_score -= (switch_count - MAX_SWITCHES) * 0.5

    return {
        "path": path,
        "total_score": adjusted_score,
        "total_time": time,
        "total_cost": cost,
        "total_risk": risk,
        "switch_count": switch_count,
        "explanation": [EdgeExplanation(**e).dict() for e in explanation],
    }

def diversify(paths, top_n=5):
    seen_patterns = set()
    results = []

    for p in paths:
        signature = tuple(p["path"][:3])  # simple diversity heuristic

        if signature in seen_patterns:
            continue

        seen_patterns.add(signature)
        results.append(p)

        if len(results) == top_n:
            break

    return results


def assign_labels(paths):
    if not paths:
        return paths

    min_wait_time = min(p["total_time"] for p in paths)
    min_cost = min(p["total_cost"] for p in paths)
    min_risk = min(p["total_risk"] for p in paths)

    for p in paths:
        labels = []

        if p["total_time"] == min_wait_time:
            labels.append(Label.FASTEST.value)

        if p["total_cost"] == min_cost:
            labels.append(Label.CHEAPEST.value)

        if p["total_risk"] == min_risk:
            labels.append(Label.MOST_RELIABLE.value)

        # balanced heuristic
        if (
            abs(p["total_time"] - min_wait_time) <= 3 and
            abs(p["total_cost"] - min_cost) <= 5
        ):
            labels.append(Label.BALANCED.value)

        p["labels"] = labels

    return paths


def compute_routes(req: PathRequest, session: Session):

    # 1. Build graph + edges once
    graph = build_graph(session)
    edge_lookup = build_edge_lookup(session)

    # 2. Generate paths (BFS)
    raw_paths = bfs_paths(graph, req.from_node_id, req.to_node_id)

    if not raw_paths:
        return []

    # 3. Prefetch snapshots for edges used across all paths to avoid N+1
    edge_ids = set()
    for path in raw_paths:
        for i in range(len(path) - 1):
            edge = edge_lookup.get((path[i], path[i+1]))
            if edge:
                edge_ids.add(edge.id)

    snapshot_cache: Dict[str, dict] = {}
    for eid in edge_ids:
        snapshot_cache[str(eid)] = get_edge_status_snapshot(eid, session)

    scored_paths = []

    # 4. Evaluate each path using cached snapshots
    for path in raw_paths:
        time, cost, risk, explanation = evaluate_path_cached(path, edge_lookup, snapshot_cache, session)

        if not _route_has_valid_edges(explanation):
            continue

        scored_paths.append(_build_route_summary(path, time, cost, risk, explanation, req.preference))

    if not scored_paths:
        return []

    # 5. Prefer routes with at least 3 options if available, but cap at 5.
    results = assign_labels(scored_paths)

    # sort by score (higher better) then neutral tie-breakers
    results.sort(key=lambda x: (-x["total_score"], x["total_time"], x["total_cost"]))

    diversified = diversify(results, top_n=MAX_ROUTES)

    # If we have more than the minimum viable set, keep the best 5.
    if len(diversified) > MAX_ROUTES:
        diversified = diversified[:MAX_ROUTES]

    return diversified[:MAX_ROUTES]