from abc import ABC, abstractmethod
from  enum import Enum
from itertools import groupby
import math
import re
import copy
from typing import Callable, Iterator, Optional, Type, TypeVar
from .ast_node import ASTNode

VERBOSE = False
class MatchUtils:

    EXACT_MATCH = 'EXACT_MATCH'

    @staticmethod
    def is_match(src: ASTNode, cmp: ASTNode)-> bool:
        return src.get_kind() == cmp.get_kind() and src.get_properties() == cmp.get_properties()

    @staticmethod
    def is_kind_match(src: ASTNode, cmp: ASTNode)-> bool:
        return src.get_kind() == cmp.get_kind()

    @staticmethod
    def is_wildcard(target: ASTNode|str)-> bool:
        return MatchUtils.is_single_wildcard(target) or MatchUtils.is_multi_wildcard(target)

    @staticmethod
    def is_multi_wildcard(target: ASTNode|str)-> bool:
        if isinstance(target, str):
            return target.startswith('$$')
        return MatchUtils.is_multi_wildcard(target.get_name())
    @staticmethod
    def is_single_wildcard(target: ASTNode|str)-> bool:
        if isinstance(target, str):
            return not MatchUtils.is_multi_wildcard(target) and target.startswith('$')
        return MatchUtils.is_single_wildcard(target.get_name())

class KeyMatch:
    def clone(self) -> 'KeyMatch':
        cloned = KeyMatch(self.key)
        cloned.nodes = self.nodes[:]
        return cloned
    
    def __init__(self, key:str) -> None:
        self.key = key
        self.nodes: list[ASTNode] = []
    def add_node(self, node: ASTNode):
        self.nodes.append(node)

class PatternMatch:
    def __init__(self, src_nodes: list[ASTNode], patterns: list[ASTNode]) -> None:
        self.keyMatches: list[KeyMatch] = []
        self.evaluated_nodes: list[ASTNode] = []
        self.src_nodes = src_nodes
        self.patterns = patterns

    def clone(self) -> 'PatternMatch':
        # create a new instance of the pattern match
        clone = PatternMatch(self.src_nodes, self.patterns)
        # clone the key matches
        clone.keyMatches = [keyMatch.clone() for keyMatch in self.keyMatches]
        clone.evaluated_nodes = self.evaluated_nodes[:]
        return clone

    def query_create(self, key: str)-> KeyMatch:
        if self.keyMatches and self.keyMatches[-1].key==key:
            return self.keyMatches[-1]
        self.keyMatches.append(KeyMatch(key))
        return self.keyMatches[-1]
   
    def get_evaluated_nodes(self)-> list[ASTNode]:
        return self.evaluated_nodes

    def add_evaluated_node(self, node: ASTNode):
        self.evaluated_nodes.append(node)
    
    def get_dict(self):
        return {keyMatch.key: keyMatch.nodes for keyMatch in self.keyMatches}

    def validate(self):
        return self._check_and_correct_single_matches() and self._check_duplicate_matches()

    def _check_and_correct_single_matches(self):
        """
        Checks for single matches in the keyMatches attribute.

        This method checks if any keyMatch has exactly  one node. If not the method returns False.

        Returns:
            bool: False if any keyMatch has more than one node, otherwise None.
        """
        #first remove potential children with the same name
        for keyMatch in self.keyMatches:
            keyMatch.nodes = [node for node in keyMatch.nodes if node.get_parent() not in keyMatch.nodes]

        result =  all(len(keyMatch.nodes) == 1 for keyMatch in self.keyMatches if MatchUtils.is_single_wildcard(keyMatch.key))
        if not result and VERBOSE:
            print(f"FAILED on single match")
        return result
    
    def _check_duplicate_matches(self):
        """
        Checks for duplicate matches in the keyMatches attribute.

        This method groups the keyMatches by their keys and identifies groups with the same key.
        It then transposes the nodes in these groups to compare nodes at the same index across different groups.
        If any group of nodes at the same index do not match, the method returns False.

        Returns:
            bool: False if any group of nodes at the same index do not match, otherwise None.
        """
        keyGroups = { key:list(sameGroups) for key, sameGroups in groupby(self.keyMatches, lambda x: x.key)}
        sameKeyGroups = {key: [ns.nodes for ns in  sameGroups] for key, sameGroups in keyGroups.items() if len(sameGroups) > 1}
        for key, same in sameKeyGroups.items():
            transposed: list[list[ASTNode]] = [list(row) for row in zip(*same)] # create tuples of nodes per index
            for matching_nodes in transposed:
                if not all(map(lambda node: MatchUtils.is_match(node, matching_nodes[0]), matching_nodes[1:])):
                    if VERBOSE:
                        print(f"FAILED on duplicate match")
                    return False
        return True

class MatchFinder:

    @staticmethod
    def find_all(srcNodes: list[ASTNode], *patterns_list: list[ASTNode], recursive=True)-> Iterator[PatternMatch]:
        """
        Finds all matches of the given patterns in the source nodes.
        Args:
            srcNodes (list[ASTNode]): The list of source nodes to search within.
            *patterns_list (list[ASTNode]): Variable length argument list of patterns to match against the source nodes.
            recursive (bool): Whether to search recursively through all children of the source nodes.
        Yields:
            Iterator[PatternMatch]: An iterator of PatternMatch objects representing the matches found.
        Note:
            - The search will yield only the first pattern matched found for source node.
            - The search will continue recursively through all children of the source nodes if recursive is true.
            - Nodes found in a match will not be included in subsequent matches.
        """
        newIndex = 0
        while newIndex < len(srcNodes):
            target_nodes = srcNodes[newIndex:]
            for patterns in patterns_list:
                pattern_match = MatchFinder.match_pattern(PatternMatch(target_nodes,patterns), target_nodes, patterns)
                newIndex += 1

                if pattern_match:
                    for included_node in pattern_match.get_evaluated_nodes():
                        if included_node in srcNodes:
                            # skip all nodes that are included in the match
                            newIndex = max(srcNodes.index(included_node)+1, newIndex)
                    yield pattern_match
                    break # only one match is needed
        #recursively include all children
        if recursive:
            for node in srcNodes:
                yield from MatchFinder.find_all(node.get_children(), *patterns_list)

    @staticmethod
    def match_pattern(patternMatch: PatternMatch, srcNodes: list[ASTNode], patterns: list[ASTNode], depth=0)-> Optional[PatternMatch]:
        """
        Matches a given pattern against a this of source nodes.
        Args:
            patternMatch (PatternMatch): The current pattern match state.
            srcNodes (list[ASTNode]): The list of source nodes to match against.
            patterns (list[ASTNode]): The list of pattern nodes to match.
        Returns:
            Optional[PatternMatch]: The updated pattern match if the pattern is successfully matched,
                                    otherwise None.
        """
        only_multi_wild_cards = all(MatchUtils.is_multi_wildcard(p) for p in patterns)
        # if there are no patterns or only wildcards left and no source nodes, return the current match
        if len(patterns) == 0 or (only_multi_wild_cards and len(srcNodes) == 0):
            # we might end up with a multi wildcard at the end of the pattern list without nodes so add it
            if only_multi_wild_cards and len(patterns) ==1 :
                patternMatch.query_create(patterns[0].get_name())

            if patternMatch.validate():
                return patternMatch
            return None

        if( len(srcNodes) == 0):
            return None

        srcNode = srcNodes[0]
        patternMatch.add_evaluated_node(srcNode)
        patternNode = patterns[0]

        indent = ' '*depth*4
        if VERBOSE:
            print(indent+ f"evaluating {srcNode.get_raw_signature()} against {patternNode.get_raw_signature()}")

        if MatchUtils.is_multi_wildcard(patternNode):
            wildcard_match = patternMatch.query_create(patternNode.get_name())
            if len(patterns) > 1:
                # multiplicity of multi-wildcards is 0 so first try to match the next pattern
                # TODO greedy approach until no match
                nextMatch = MatchFinder.match_pattern(patternMatch.clone(), srcNodes, patterns[1:], depth)
                if nextMatch:                 
                    return nextMatch  
            if VERBOSE:
                print(indent+ f"  multi wildcard {patternNode.get_raw_signature()} matched {srcNode.get_raw_signature()}")
            wildcard_match.add_node(srcNode)
            return MatchFinder.match_pattern(patternMatch, srcNodes[1:], patterns, depth)
        elif MatchUtils.is_single_wildcard(patternNode) or MatchUtils.is_match(srcNode, patternNode):
            # in case of children the kind must also match (which is not checked for wildcard yet)
            if patternNode.get_children() and (not MatchUtils.is_kind_match(srcNode, patternNode)):
                return None

            if MatchUtils.is_single_wildcard(patternNode):
                wildcard_match = patternMatch.query_create(patternNode.get_name())
                wildcard_match.add_node(srcNode)
            if VERBOSE:
                print(indent+ f"  {patternNode.get_raw_signature()} matched {srcNode.get_raw_signature()}")

            if patternNode.get_children():
                foundMatch =  MatchFinder.match_pattern(patternMatch, srcNode.get_children(), patternNode.get_children(),depth+1)
                if not foundMatch:
                    return None
                patternMatch = foundMatch
            # invariant: a match is found if the current nodes match and their successors match
            return MatchFinder.match_pattern(patternMatch, srcNodes[1:], patterns[1:], depth)
        return None

