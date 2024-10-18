from impl.clang import ClangASTNode
import logging

from unittest import TestCase

from syntax_tree.ast_factory import ASTFactory
from syntax_tree.ast_shower import ASTShower
from syntax_tree.c_pattern_factory import CPatternFactory
from test.clang.clang_model_loader import ClangModelLoader
from parameterized import parameterized

logger = logging.getLogger(__name__)

class TestCPatternFactory(TestCase):
    logger.info("Loading AST")
    model = ClangModelLoader.model
    logger.info("Loaded AST")

    @parameterized.expand([
        ('a == $hallo',),
        ('b != $world',),
        ('c > $foo',),
        ('d < $bar',),
        ('e >= $baz',),
        ('f <= $qux',)
    ])
    def test_expression(self, expression):
        factory = ASTFactory(ClangASTNode)
        patternFactory = CPatternFactory(factory)
        ASTShower.show_node(patternFactory.create_expression(expression))
