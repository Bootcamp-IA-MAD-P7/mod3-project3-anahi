from src.graph.builder import build_graph


def test_graph_compiles_without_error():
    graph = build_graph()
    assert graph is not None


def test_graph_has_expected_nodes():
    graph = build_graph()
    node_names = set(graph.nodes.keys())
    expected = {
        "router_node",
        "arxiv_rag_node",
        "news_rag_node",
        "llm_node",
        "linkedin_node",
        "instagram_node",
        "medium_node",
        "substack_node",
        "image_node",
    }
    assert expected.issubset(node_names)
