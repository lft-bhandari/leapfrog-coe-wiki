from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

_MOCK_GRAPH = {
    "nodes": [{"id": "domains/general/index", "type": "domain", "label": "General"}],
    "edges": [],
}


def test_get_graph_returns_200_with_nodes_and_edges():
    with patch("app.routers.graph.build_graph", return_value=_MOCK_GRAPH):
        response = client.get("/api/graph")

    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data


def test_get_graph_response_contains_domain_nodes():
    with patch("app.routers.graph.build_graph", return_value=_MOCK_GRAPH):
        response = client.get("/api/graph")

    nodes = response.json()["nodes"]
    assert any(n["type"] == "domain" for n in nodes)
