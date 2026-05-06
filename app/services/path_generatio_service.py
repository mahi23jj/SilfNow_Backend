from collections import defaultdict, deque
from sqlmodel import select, Session

from app.models.edge import Edge

def build_graph(session: Session):
    edges = session.exec(select(Edge)).all()

    graph = defaultdict(list)

    for edge in edges:
        graph[edge.from_node_id].append(edge.to_node_id)

    return graph


def bfs_paths(graph, start, end, max_depth=3):
    queue = deque()
    queue.append((start, [start]))

    all_paths = []

    while queue:
        node, path = queue.popleft()

        # depth limit (number of edges)
        if len(path) - 1 > max_depth:
            continue

        # reached destination
        if node == end:
            all_paths.append(path)
            continue

        # expand neighbors from in-memory graph
        for neighbor in graph.get(node, []):

            # avoid cycles
            if neighbor in path:
                continue

            queue.append((neighbor, path + [neighbor]))

    return all_paths