from dataclasses import dataclass, field
from functools import cache, lru_cache
from json import JSONDecodeError
import json
from typing import List, Optional
from typing_extensions import override

from syntax_tree.ast_node import ASTNode
from dataclasses_json import dataclass_json, config

@dataclass_json
@dataclass(frozen=True)
class Position:
    offset: Optional[int] = 0
    line: Optional[int] = 0
    col: Optional[int] = 0
    tokLen: Optional[int] = 0
    file: Optional[str] = None
    includedFrom: Optional[dict] = None

@dataclass_json
@dataclass(frozen=True)
class ExtendedPosition(Position):
    spellingLoc: Optional[Position] = Position()
    expansionLoc: Optional[Position] = Position()

@dataclass_json
@dataclass(frozen=True)
class EmptyDict:
    pass

@dataclass_json
@dataclass(frozen=True)
class Range:
    begin: ExtendedPosition
    end: ExtendedPosition

@dataclass_json
@dataclass(frozen=True)
class Type:
    qualType: str
    desugaredQualType: Optional[str] = None

@dataclass_json
@dataclass(frozen=True)
class Decl:
    id: str
    kind: str
    name: Optional[str] = None

@dataclass_json
@dataclass(frozen=True)
class ClangASTNode(ASTNode):
    id: str
    kind: str
    loc: Optional[Position] = Position()
    range: Optional[Range] = Range(begin=ExtendedPosition(), end= ExtendedPosition())
    valueCategory: Optional[str] = None
    value: Optional[str] = None
    castKind: Optional[str] = None
    decl: Optional[Decl] = None
    type: Optional[Type] = None
    isImplicit: Optional[bool] = None
    tagUsed: Optional[str] = None
    isUsed: Optional[str] = None
    name: Optional[str] = None
    mangledName: Optional[str] = None
    implicit: Optional[bool] = None
    children: Optional[list['ClangASTNode']] = field(default=None, metadata=config(field_name="inner"))
    parent: Optional['ClangASTNode'] = field(default=None, repr=False, compare=False, hash=False, init=False)

    def __post_init__(self):
        if self.children:
            for child in self.children:
                self._set_parent(child)
        else:
            object.__setattr__(self, 'children', [])


    def _set_parent(self, child: 'ClangASTNode') -> 'ClangASTNode':
        object.__setattr__(child, 'parent', self)
        return child
    
    # Function to get the schema
    @staticmethod
    @lru_cache(maxsize=None)
    def get_schema():
        return ClangASTNode.schema() #type: ignore
    
    @staticmethod
    def load(file) -> 'ClangASTNode' :
        with open(file, 'r') as f:
            data = f.read()
            try:
                schema = ClangASTNode.get_schema()
                return schema.load(json.loads(data))
                # return ClangASTNode.from_json(data) # type: ignore
            except JSONDecodeError as e:
                print(f"JSON Decode Error: {e.msg}")
                print(f"Line number: {e.lineno}")
                print(f"Column number: {e.colno}")
                raise e
            except KeyError as e:
                print(f"JSON KeyError: {e}")
                raise e
            except Exception as e:
                print(f"Error: {e}")            
                raise e

    @override
    @cache
    def get_containing_filename(self) -> str:
        return self.loc.file if self.loc and self.loc.file else ""
    
    @override
    @cache
    def get_start_offset(self) -> int: 
        return self.loc.offset if self.loc and self.loc.offset else 0

    @override
    def get_length(self) -> int: 
        return self.loc.tokLen if self.loc and self.loc.tokLen else 0

    @override
    @cache
    def get_kind(self) -> str: 
        return self.kind

    @override
    @cache
    def getProperties(self) -> dict[str, int|str]: 
        return {}
    
    @override
    @cache
    def get_parent(self) -> Optional['ClangASTNode']: 
        self.parent

    @override
    @cache
    def get_children(self) -> list['ClangASTNode']: 
        return self.children if self.children else []

    @override
    @cache
    def get_name(self) -> str:
        return self.name if self.name else ""
    
ClangASTNode.__annotations__['children'] = List[ClangASTNode]
ClangASTNode.__annotations__['parent'] = ClangASTNode
