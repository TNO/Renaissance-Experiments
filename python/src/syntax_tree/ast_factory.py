from pathlib import Path
from typing import TypeVar

from impl.clang.clang_ast_node import ClangASTNode
from syntax_tree.ast_node import ASTNode
from syntax_tree.ast_shower import ASTShower

ASTNodeType = TypeVar("ASTNodeType", bound='ASTNode')

class ASTFactory:

    def __init__(self, clazz: type[ASTNodeType]) -> None: 
        self.clazz = clazz

    def create(self, file_path: Path):  
        return self.clazz.load(file_path=file_path)

    def create_from_text(self, text:str, file_name:str):  
        return self.clazz.load_from_text(text, file_name)

if __name__ == "__main__":
    pass

