from renaissance.syntax_tree.match_finder import is_match
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


def test_matcher_prefers_semantic_kind_over_legacy_type():
    source = FakeNode()
    pattern = FakeNode()
    source.semantic_kind = SemanticKind.CALL
    pattern.semantic_kind = SemanticKind.CALL
    source.ast_type = object()
    pattern.ast_type = object()

    assert is_match(source, pattern)
