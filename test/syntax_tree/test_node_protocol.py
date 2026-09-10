from renaissance.syntax_tree.node_protocol import NodeProtocol
from renaissance.syntax_tree.semantic_kind import SemanticKind


class FakeNode:
    ast_type = object()
    parser_kind = "fake_node"
    semantic_kind = SemanticKind.NODE
    properties = {}
    children = []
    signature = "fake"
    name = ""


def test_structural_node_satisfies_protocol():
    assert isinstance(FakeNode(), NodeProtocol)
