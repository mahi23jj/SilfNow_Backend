from app.services.path_generatio_service import bfs_paths


def test_bfs_simple():
    graph = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["D"],
        "D": [],
    }

    paths = bfs_paths(graph, "A", "D", max_depth=3)

    assert ["A", "B", "D"] in paths
    assert ["A", "C", "D"] in paths
    assert len(paths) == 2
