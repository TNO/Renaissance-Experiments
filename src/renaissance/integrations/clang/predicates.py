from renaissance.syntax_tree.node_protocol import NodeProtocol

TYPE_REFERENCE_KINDS = frozenset({"TypeRef", "TYPE_REF", "type_identifier"})
DECLARATION_REFERENCE_KINDS = frozenset({"DeclRefExpr", "DECL_REF_EXPR"})
COMPOUND_STATEMENT_KINDS = frozenset({"CompoundStmt", "COMPOUND_STMT"})
MACRO_DEFINITION_KINDS = frozenset({"MacroDefinition", "MACRO_DEFINITION"})
METHOD_KINDS = frozenset({"CXXMethodDecl", "CXX_METHOD"})
CONSTRUCTOR_KINDS = frozenset({"CXXConstructorDecl", "CXX_CONSTRUCTOR"})


def is_clang_kind(node: NodeProtocol, *parser_kinds: str) -> bool:
    return node.parser_kind in parser_kinds


def is_clang_type_reference(node: NodeProtocol) -> bool:
    return node.parser_kind in TYPE_REFERENCE_KINDS


def is_clang_declaration_reference(node: NodeProtocol) -> bool:
    return node.parser_kind in DECLARATION_REFERENCE_KINDS


def is_clang_compound_statement(node: NodeProtocol) -> bool:
    return node.parser_kind in COMPOUND_STATEMENT_KINDS


def is_clang_macro_definition(node: NodeProtocol) -> bool:
    return node.parser_kind in MACRO_DEFINITION_KINDS


def is_clang_method(node: NodeProtocol) -> bool:
    return node.parser_kind in METHOD_KINDS


def is_clang_constructor(node: NodeProtocol) -> bool:
    return node.parser_kind in CONSTRUCTOR_KINDS
