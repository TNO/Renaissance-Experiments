import logging

from unittest import TestCase

from impl.clang import ClangASTNode
from syntax_tree.ast_factory import ASTFactory

logger = logging.getLogger(__name__)

class TestASTFactory(TestCase):
    factory = ASTFactory(ClangASTNode)

    def createRoot(self):
        return TestASTFactory.factory.create_from_text('int main() { return 0; }', "test.c")

    def test_canCreateAST(self):
        self.assertTrue(self.createRoot())

