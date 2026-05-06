from types import SimpleNamespace

from app.services.path_ranking_service import compute_routes


def _edge(edge_id, bus_cost=1.0, taxi_cost=4.0, bus_time=5, taxi_time=8):
    return SimpleNamespace(
        id=edge_id,
        base_travel_time_min=bus_time,
        base_travel_time_max=taxi_time,
        base_cost_min=bus_cost,
        base_cost_max=taxi_cost,
    )


def test_compute_routes_filters_bad_routes_and_limits_top_results():
    graph = {
        "A": ["B", "C", "D"],
        "B": ["E"],
        "C": ["E"],
        "D": ["E"],
    }

    edges = {
        ("A", "B"): _edge("ab"),
        ("B", "E"): _edge("be"),
        ("A", "C"): _edge("ac"),
        ("C", "E"): _edge("ce"),
        ("A", "D"): _edge("ad"),
        ("D", "E"): _edge("de"),
    }

    snapshots = {
        "ab": {"statuses": [{"transport_type": "bus", "queue_level": "LOW", "vehicle_availability": "AVAILABLE", "estimated_wait_time": 2, "confidence": 0.9, "num_reports": 10, "stability": "MODERATE"}]},
        "be": {"statuses": [{"transport_type": "taxi", "queue_level": "LOW", "vehicle_availability": "AVAILABLE", "estimated_wait_time": 1, "confidence": 0.9, "num_reports": 10, "stability": "MODERATE"}]},
        "ac": {"statuses": [{"transport_type": "taxi", "queue_level": "LOW", "vehicle_availability": "UNAVAILABLE", "estimated_wait_time": 1, "confidence": 0.9, "num_reports": 10, "stability": "MODERATE"}]},
        "ce": {"statuses": [{"transport_type": "bus", "queue_level": "HIGH", "vehicle_availability": "AVAILABLE", "estimated_wait_time": 40, "confidence": 0.9, "num_reports": 10, "stability": "MODERATE"}]},
        "ad": {"statuses": [{"transport_type": "bus", "queue_level": "LOW", "vehicle_availability": "AVAILABLE", "estimated_wait_time": 2, "confidence": 0.15, "num_reports": 1, "stability": "MODERATE"}]},
        "de": {"statuses": [{"transport_type": "bus", "queue_level": "LOW", "vehicle_availability": "AVAILABLE", "estimated_wait_time": 2, "confidence": 0.95, "num_reports": 10, "stability": "MODERATE"}]},
    }

    req = SimpleNamespace(from_node_id="A", to_node_id="E", preference="balanced")

    session = SimpleNamespace()

    from unittest.mock import patch

    with patch("app.services.path_ranking_service.build_graph", return_value=graph), \
         patch("app.services.path_ranking_service.build_edge_lookup", return_value=edges), \
         patch("app.services.path_ranking_service.bfs_paths", return_value=[["A", "B", "E"], ["A", "C", "E"], ["A", "D", "E"]]), \
         patch("app.services.path_ranking_service.get_edge_status_snapshot", side_effect=lambda edge_id, _session: snapshots[str(edge_id)]):
        routes = compute_routes(req, session)

    assert len(routes) == 1
    assert routes[0]["path"] == ["A", "B", "E"]
    assert routes[0]["labels"]
