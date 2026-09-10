import tree_sitter_python

from renaissance.integrations.tree_sitter.adapter import TreeSitterAdapter
from renaissance.syntax_tree.semantic_kind import SemanticKind


def test_tree_sitter_nodes_expose_protocol_metadata():
    adapter = TreeSitterAdapter(tree_sitter_python)
    root = adapter.to_lst("def f():\n    return 1\n", adapter.parse_code("def f():\n    return 1\n")).root

    assert root.parser_kind == "module"
    assert root.semantic_kind is SemanticKind.TRANSLATION_UNIT
    assert root.children[0].parser_kind == "function_definition"
    assert root.children[0].semantic_kind is SemanticKind.FUNCTION
