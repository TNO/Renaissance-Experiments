from enum import StrEnum


class SemanticKind(StrEnum):
    NODE = "node"
    TRANSLATION_UNIT = "translation_unit"
    STATEMENT = "statement"
    EXPRESSION = "expression"
    DECLARATION = "declaration"
    DEFINITION = "definition"
    NAME = "name"
    LITERAL = "literal"
    CALL = "call"
    FUNCTION = "function"
    CLASS = "class"
    ASSIGNMENT = "assignment"
    BINARY_OPERATION = "binary_operation"
    UNARY_OPERATION = "unary_operation"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    RETURN = "return"
    IMPORT = "import"
    PARAMETER = "parameter"
    COMMENT = "comment"
