# create a class that inherits syntax tree ASTNode

from functools import cache
import json
from syntax_tree.ast_node import ASTNode
from typing import Any, Optional
from typing_extensions import override


EMPTY_DICT = {}
EMPTY_STR = ''
EMPTY_LIST = []
class ClangJsonASTNode(ASTNode):
    def __init__(self, node: dict[str, Any], parent: Optional['ClangJsonASTNode'] = None):
        self.node = node
        self._children: Optional[list['ClangJsonASTNode']] = None
        self.parent = parent

    @staticmethod
    def load(file_path) -> 'ClangJsonASTNode':
        with open(file_path, 'r') as f:
            return ClangJsonASTNode(json.load(f))

    @override
    def get_containing_filename(self) -> str:
        return self.node.get('loc', EMPTY_DICT).get('file', EMPTY_STR)
    
    @override
    def get_start_offset(self) -> int: 
        return self.node.get('loc', EMPTY_DICT).get('offset', 0)

    @override
    def get_length(self) -> int: 
        return self.node.get('loc', EMPTY_DICT).get('tokLen', 0)

    @override
    def get_kind(self) -> str: 
        return self.node.get('kind', EMPTY_STR)

    @override
    def getProperties(self) -> dict[str, int|str]: 
        return EMPTY_DICT
    
    @override
    def get_parent(self) -> Optional['ClangJsonASTNode']: 
        return self.parent

    @override
    def get_children(self) -> list['ClangJsonASTNode']: 
        if self._children is None:
            self._children = [ ClangJsonASTNode(n, self) for n in self.node.get('inner', [])]
        return self._children
    
    @override
    def get_name(self) -> str:
        return self.node.get('name', EMPTY_STR)
