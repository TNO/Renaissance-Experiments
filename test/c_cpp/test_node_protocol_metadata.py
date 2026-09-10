from pathlib import Path

from renaissance.integrations.clang.clang_json_ast_node import ClangJsonASTNode
from renaissance.syntax_tree.semantic_kind import SemanticKind


def test_clang_json_nodes_expose_protocol_metadata():
    node = ClangJsonASTNode.load_from_text("int f() { return 1; }", "test.c", [], Path())

    assert node.parser_kind == "TranslationUnitDecl"
    assert node.semantic_kind is SemanticKind.TRANSLATION_UNIT
