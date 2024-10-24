import logging
from unittest import TestCase
from impl.clang.clang_ast_node import ClangASTNode
from parameterized import parameterized
from syntax_tree.ast_factory import ASTFactory
from syntax_tree.ast_shower import ASTShower
from syntax_tree.c_pattern_factory import CPatternFactory
from syntax_tree.match_finder import MatchFinder
from syntax_tree.ast_node import ASTNode

import re
from .clang_model_loader import ClangModelLoader

logger = logging.getLogger(__name__)

class TestMatchFinder(TestCase):
    logger.info("Loading AST")
    factory = ASTFactory(ClangASTNode)
    patternFactory = CPatternFactory(factory)

    logger.info("Loaded AST")
            #generate cpp code in str containing if and while statements
    SIMPLE_CPP  = """
        void f(){
            int a = 3;
            int b = 4;
            if(a == 3){
                b=5;
            }
            else{
                b--;
            }
            while(a != 3){
                if  (a == 4 && b == 5){
                    b = a;
                }
            }
        }
        """



    def do_test(self, cpp_code, patterns:list[ASTNode], expected_dicts_per_match: list[dict[str, list[str]]] ,recursive: bool):

        atu = TestMatchFinder.factory.create_from_text(cpp_code, "test.cpp")
        ASTShower.show_node(atu)
        #find all if and while statements
        matches = list(MatchFinder.find_all([atu],patterns,recursive=recursive))
        for match in matches:
            print(f'\nmatch({[compress(p.get_raw_signature()) for p in match.patterns]})'+'{')
            print(f"  start node: {compress(match.src_nodes[0].get_raw_signature())}")
            for k, vs in match.get_dict().items():
                # right align the key
                print(f"{k.rjust(12)}: {[compress(v.get_raw_signature()) for v in vs]}")
            print('}')
        print('    expected dict should look like:')
        print(f'      {[to_string(match.get_dict()) for match in matches]}')
        for match, expected_dict in zip(matches, expected_dicts_per_match):
            self.assertDictEqual(to_string(match.get_dict()), expected_dict)
        self.assertEqual(len(matches), len(expected_dicts_per_match))
        return matches

class TestExpressions(TestMatchFinder):
        
    @parameterized.expand([
    ('a == 3',['a==3'], [{}]),   
    ('a == $x',['a==3', 'a==4'], [{'$x':['3']},{'$x':['4']}]),
    ('$y == $x',['a==3', 'a==4', 'b==5'], [{'$y':['a'], '$x':['3']},{'$y':['a'], '$x':['4']},{'$y':['b'], '$x':['5']}]),
])
    def test(self, expression, expected_full_matches: list[str], expected_dicts_per_match: list[dict[str, list[str]]]):
        exprNode = self.patternFactory.create_expression(expression)
        matches = self.do_test(TestStatements.SIMPLE_CPP, [exprNode], expected_dicts_per_match, recursive=True)
        self.assertEqual([compress(match.src_nodes[0].get_raw_signature()) for match in matches], expected_full_matches)

class TestStatements(TestMatchFinder):
        
    @parameterized.expand([
    ('{$x;$y;}',[{'$x':['int a=3;'], '$y':['int b=4;']}]),   
    ('if($x){$$stmts;}',[{'$x': ['a==3'], '$$stmts': ['b=5']}, {'$x': ['a==4&&b==5'], '$$stmts': ['b=a']}]),
    ('if($x){$$stmts;}else{$single;$$multi}',[{'$x': ['a==3'], '$$stmts': ['b=5'], '$single': ['b--'], '$$multi': []}]),
    ('if($x){$$stmts;}else{$$multi;$single;}',[{'$x': ['a==3'], '$$stmts': ['b=5'], '$single': ['b--'], '$$multi': []}]),
    ('while(a!=$x){$$stmts;}',[{'$x': ['3'], '$$stmts': ['if(a==4&&b==5){b=a;}']}]),
])
    def test(self, statements, expected_dicts_per_match: list[dict[str, list[str]]]):
        stmtNodes = self.patternFactory.create_statements(statements)
        self.do_test(TestStatements.SIMPLE_CPP, stmtNodes, expected_dicts_per_match, recursive=True)

class TestFunctionCallStatements(TestMatchFinder):

    #TODO there are some issues with multiplictity or argments in match_finder , need to fix it
    @parameterized.expand([
    ('$f($a);',['int (*fp) $f;'],[{'$f': ['one(a)'], '$a': ['a']}]),   
    ('$f($a, $$all);',['int (*fp) $f;'],[{'$f': ['one(a)'], '$a': ['a'], '$$all': []}, {'$f': ['two(a,b)'], '$a': ['a'], '$$all': ['b']}, {'$f': ['three(a,b,c)'], '$a': ['a'], '$$all': ['b', 'c']}]),
    ('$f($$all, $a);',['int (*fp) $f;'],[{}]),
    ('$f($a, $$all, $b);',['int (*fp) $f;'],[{}]),
])
    def test_function(self, statements, extra_declarations, expected_dicts_per_match: list[dict[str, list[str]]]):
        code = """
        int one(int a);
        int two(int a, int b);
        int three(int a, int b, int c);
        int a,b,c;
        void f(){
            one(a);
            two(a,b)
            three(a,b,c);
        }
        """
        
        stmtNodes = self.patternFactory.create_statements(statements, extra_declarations=extra_declarations)
        ASTShower.show_node(stmtNodes[0])
        self.do_test(code, stmtNodes, expected_dicts_per_match, recursive=True)

def to_string(d:dict[str, list[ASTNode]]):
    return {k: [compress(v.get_raw_signature()) for v in vs] for k, vs in d.items()}

def compress(s:str):
    skip_whitespace =  re.sub(r'\s+', ' ',s.replace('\n',''))
    skip_whitespace = re.sub(r'(\W)\s', r'\1',skip_whitespace)
    skip_whitespace = re.sub(r'\s(\W)', r'\1',skip_whitespace)
    return skip_whitespace
