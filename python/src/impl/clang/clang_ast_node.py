from functools import cache
from pathlib import Path
from typing import Optional
from syntax_tree.ast_node import ASTNode
from typing_extensions import override

from clang.cindex import TranslationUnit, Index, Config

EMPTY_DICT = {}
EMPTY_STR = ''
EMPTY_LIST = []
class ClangASTNode(ASTNode):
    print(Path(__file__).parent.parent.parent.parent / '.venv/Lib/site-packages/clang/native')
    Config.set_library_path(Path(__file__).parent.parent.parent.parent / '.venv/Lib/site-packages/clang/native')
    index = Index.create()
    parse_args=['-fparse-all-comments', '-ferror-limit=0', '-Xclang', '-ast-dump', '-fsyntax-only']

    def __init__(self, node, translation_unit:TranslationUnit,  parent =  None):
        super().__init__(self if parent is None else parent.root)
        self.node = node
        self._children = None
        self.parent = parent
        self.translation_unit = translation_unit

    @override
    @staticmethod
    def load(file_path: Path) -> 'ClangASTNode':
        translation_unit: TranslationUnit = ClangASTNode.index.parse(file_path, args=ClangASTNode.parse_args)
        return ClangASTNode(translation_unit.cursor, translation_unit, None)

    @override
    @staticmethod
    def load_from_text(file_content: str, file_name: str='test.c') -> 'ClangASTNode':
        translation_unit: TranslationUnit = ClangASTNode.index.parse(file_name, unsaved_files=[(file_name, file_content)],  args=ClangASTNode.parse_args)
        rootNode =  ClangASTNode(translation_unit.cursor, translation_unit, None)
        # Convert file_content to bytes
        file_content_bytes = file_content.encode('utf-8')
        # add to cache to avoid reading the file again
        rootNode.cache[file_name] = file_content_bytes
        return rootNode
    
    @override
    def get_name(self) -> str:
        return self.node.spelling  #TODO fix

    @override
    def get_containing_filename(self) -> str:
        if self is self.root:
            return self.translation_unit.spelling
        try: 
            return self.node.location.file.name 
        except:
            return EMPTY_STR
    
    @override
    def get_start_offset(self) -> int: 
        try: 
            return self.node.extent.start.offset
        except:
            return 0

    @override
    @cache
    def get_length(self) -> int: 
        try: 
            endOffset =  self.node.extent.end.offset
            return endOffset - self.get_start_offset()
        except:
            return 0

    @override
    def get_kind(self) -> str: 
        return str(self.node.kind.name) 

    @override
    def getProperties(self) -> dict[str, int|str]: 
        return EMPTY_DICT
    
    @override
    def get_parent(self) -> Optional['ClangASTNode']: 
        return self.parent

    @override
    def get_children(self) -> list['ClangASTNode']: 
        if self._children is None:
            self._children = [ ClangASTNode(n, self.translation_unit, self) for n in self.node.get_children()]
        return self._children

# Function to recursively visit AST nodes
def visit_node(node, depth=0):
    print('  ' * depth + f'{node.kind} {node.spelling}')
    for child in node.get_children():
        visit_node(child, depth + 1)

if __name__ == "__main__":
    pass
    # Set the path to libclang.so
    # clang.cindex.Config.set_library_file('C:/Users/pnelissen/scoop/apps/llvm/current/bin/libclang.dll')
    # root = ClangASTNode.load(Path('Z:/testproject/c/src/main.c'))

    # root.translation_unit.save('Z:/testproject/c/src/main.c.ast')

    # def visitFunction(astNode: ASTNode) -> None:
    #     parent = astNode.get_parent()
    #     depth = 0
    #     while parent:
    #         depth += 1
    #         parent = parent.get_parent()
    #     print(str('  ' * depth) + astNode.get_kind())

    # # root.process(visitFunction)

    # ASTShower.show_node(root)
