

from pathlib import Path
from impl.clang.clang_ast_node import ClangASTNode


class ClangModelLoader():
    model = ClangASTNode.load(Path(__file__).parent.parent.parent.parent / 'c/src/main.c')
