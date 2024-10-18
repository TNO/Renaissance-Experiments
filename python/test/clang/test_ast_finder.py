from pathlib import Path
from impl.clang import ClangASTNode
import logging
import time

from unittest import TestCase

from syntax_tree import ASTFinder, ASTNode

from test.clang.clang_model_loader import ClangModelLoader

logger = logging.getLogger(__name__)



class TestFinder(TestCase):
    model = ClangModelLoader.model

class TestKindFinder(TestFinder):

    def test_findBogus(self):
        iter = ASTFinder.find_kind(TestKindFinder.model, '.*Bogus.*')
        total = len(list(iter))
        self.assertEqual( total, 0)
        print( total)

    def test_findExpr(self):
        iter = ASTFinder.find_kind(TestKindFinder.model, '.*EXPR.*')
        total = len(list(iter))
        self.assertGreater( total, 0)
        print( total)


class TestAllFinder(TestFinder):

    def test_findAllBogus(self):
        def isBogus(node: ASTNode):
            if 'Bogus' in node.get_kind(): yield node
        iter = ASTFinder.find_all(TestAllFinder.model, isBogus)
        total = len(list(iter))
        self.assertEqual( total, 0)
        print( total)

    def test_findExpr(self):
        def isBinaryOperator(node: ASTNode):
            if 'BINARY_OPERATOR' in node.get_kind(): yield node
        iter = ASTFinder.find_all(TestAllFinder.model, isBinaryOperator)
        total = len(list(iter))
        self.assertGreater( total, 0)
        print( total)
