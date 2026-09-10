from more_itertools import flatten

from renaissance.syntax_tree import ASTProcessor
from renaissance.syntax_tree.ast_finder import find_semantic_kind
from renaissance.syntax_tree.semantic_kind import SemanticKind


class CleanupRefactoring:
    def __init__(self):
        raise Exception("This class should not be instantiated")

    @staticmethod
    def remove_unused_variables(ast_refactor: ASTProcessor) -> None:
        """Removes all unused variables from a function."""
        refs = flatten(
            find_semantic_kind(n, SemanticKind.DECLARATION) for n in find_semantic_kind(ast_refactor.node, SemanticKind.STATEMENT)
        )
        [ast_refactor.remove(ref.parent, True, True) for ref in refs if len(ref.referenced_by) == 0]
