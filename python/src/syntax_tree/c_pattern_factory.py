import re

from syntax_tree.ast_factory import ASTFactory
from syntax_tree.ast_finder import ASTFinder
from syntax_tree.ast_shower import ASTShower

class CPatternFactory:

    def __init__(self, factory: ASTFactory):
        self.factory = factory


    def create_expression(self, text:str):
        root =  self._create( '$variable = (' + text +');')
        #return the first expression found in the tree as a ASTNode
        return next(ASTFinder.find_kind(root, 'PAREN_EXPR')).get_children()[0]

    def _create(self, text:str):  
        keywords = CPatternFactory._get_keywords_fromText(text)
        fullText = '\n'.join(CPatternFactory._to_declaration(keywords)) + f'int __reserved__ =({text})'
        atu =  self.factory.create_from_text( fullText, 'test.cpp')
        ASTShower.show_node(atu)
        return atu

    @staticmethod
    def _get_keywords_fromText(text:str) -> list[str]:
        # regex to get keywords that start with one of two dollars followed by a \\w+
        pattern = re.compile(r'\${0,2}[a-zA-Z]\w*')
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _get_dollar_keywords_fromText(text:str) -> list[str]:
        # regex to get keywords that start with one of two dollars followed by a \\w+
        pattern = re.compile(r'\${1,2}[a-zA-Z]\w*')
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _get_non_dollar_keywords_fromText(text:str, prefix: str ='void* ', postfix: str =';') -> list[str]:
        pattern = re.compile(r'[^\$][a-zA-Z]\w*')
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _to_declaration(keywords:list[str], prefix: str ='int ', postfix: str =';') -> list[str]:
        return  [ prefix + keyword + postfix for keyword in keywords]


if __name__ == "__main__":
    print(CPatternFactory._get_dollar_keywords_fromText('struct $type;struct $name; $type a = $name; int b = 4; $$x = $$y'))
    # factory = ASTFactory(ClangASTNode)
    # patternFactory = CPatternFactory(factory)
    # ASTShower.show_node(patternFactory.create_expression('a == $hallo'))



