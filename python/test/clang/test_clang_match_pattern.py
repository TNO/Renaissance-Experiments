import logging

from unittest import TestCase

from impl.clang import ClangASTNode

from syntax_tree.ast_factory import ASTFactory
from syntax_tree.ast_shower import ASTShower

from clang.cindex import CursorKind
logger = logging.getLogger(__name__)

class TestClangMatchPattern(TestCase):
    factory = ASTFactory(ClangASTNode)

    def create(self, text:str):
        print('\n'+text)
        root = TestClangMatchPattern.factory.create_from_text(text, 'test.cpp')
        def find_unresolved_entities(node):
            for child in node.get_children():
                if child.kind ==CursorKind.is_unexposed:
                    print(f'Unexposed: {child.spelling} at {child.location}')
                elif child.kind ==CursorKind.is_invalid:
                    print(f'Invalid: {child.spelling} at {child.location}')
                find_unresolved_entities(child)
        assert isinstance(root, ClangASTNode)
        find_unresolved_entities(root.node)        
        ASTShower.show_node(root)
        return root

    def test_can_create_statement(self):
        return self.create('int a = 3;')

    def test_can_create_expression(self):
        return self.create('a = 3')

    def test_can_create_declaration(self):
        return self.create('int a = OK;')
    
    def test_can_create_dollars(self):
        return self.create('struct $type;struct $name; $type a = $name; int b = 4;')


