from abc import ABC, abstractmethod
from  enum import Enum
import re
from typing import Callable, Iterator, Type, TypeVar
from .ast_node import ASTNode

ASTNodeType = TypeVar("ASTNodeType", bound='ASTNode')

class ASTFinder:
    @staticmethod
    def find_all(astNode: ASTNodeType, function: Callable[[ASTNodeType], Iterator[ASTNodeType]])-> Iterator[ASTNodeType]:
        yield from function(astNode)
        for child in astNode.get_children():
            yield from ASTFinder.find_all(child, function)

    @staticmethod
    def find_kind(astNode: ASTNodeType, kind: str)-> Iterator[ASTNodeType]:
        pattern = re.compile(kind)
        def match(target: ASTNodeType) -> Iterator[ASTNodeType]:
            if (pattern.match(target.get_kind())):
                yield target
        yield from ASTFinder.find_all(astNode, match)
