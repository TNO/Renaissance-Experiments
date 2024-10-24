from abc import ABC, abstractmethod
from  enum import Enum
from itertools import groupby
import math
import re
import copy
from typing import Callable, Iterator, Optional, Type, TypeVar
from .ast_node import ASTNode

ASTNodeType = TypeVar("ASTNodeType", bound='ASTNode')

class MatchUtils:

    EXACT_MATCH = 'EXACT_MATCH'

    @staticmethod
    def is_match(src: ASTNode, cmp: ASTNode)-> bool:
        return src.get_kind() == cmp.get_kind() and src.get_properties() == cmp.get_properties()
    
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
        self.src_nodes = src_nodes
        self.patterns = patterns

    def clone(self) -> 'PatternMatch':
        # create a new instance of the pattern match
        clone = PatternMatch(self.src_nodes, self.patterns)
        # clone the key matches
        clone.keyMatches = [keyMatch.clone() for keyMatch in self.keyMatches]
        return clone

    def query_create(self, key: str)-> KeyMatch:
        if self.keyMatches and self.keyMatches[-1].key==key:
            return self.keyMatches[-1]
        self.keyMatches.append(KeyMatch(key))
        return self.keyMatches[-1]
    def collect_nodes(self)-> list[ASTNode]:
        return [node for keyMatch in self.keyMatches for node in keyMatch.nodes]

    def validate(self):
        return self._reassign_consecutive_wildcards() and self._check_single_matches() and self._check_duplicate_matches()

    def _get_consecutive_wildcards(self)-> Iterator[list[KeyMatch]]:
        consecutiveMatches = []
        for match in self.keyMatches:
            if (MatchUtils.is_wildcard(match.key)):
                consecutiveMatches.append(match)
            else:   
                if len(consecutiveMatches) > 1:
                    yield consecutiveMatches
                consecutiveMatches = []
        if len(consecutiveMatches) > 1:
            yield consecutiveMatches

    def _reassign_consecutive_wildcards(self) -> bool:
        """
        Reassigns nodes to consecutive wildcards in the pattern.
        This method processes consecutive wildcards in the pattern and attempts to reassign nodes to them.
        It ensures that each single wildcard gets exactly one node and multi-wildcards get the remaining nodes.
        If there are not enough nodes to assign to all single wildcards, the method returns False.
        Returns:
            bool: True if the reassignment is successful, False otherwise.
        """
        for consecutive_matches in self._get_consecutive_wildcards():
            count_single_wildcards = sum(1 for match in consecutive_matches if MatchUtils.is_single_wildcard(match.key))
            count_multi_wildcards = sum(1 for match in consecutive_matches if MatchUtils.is_multi_wildcard(match.key))
            collected_nodes =  [node for nodes in consecutive_matches for node in nodes.nodes]
            if len(collected_nodes) < count_single_wildcards:
                # cannot assign a node to all single wildcards
                return False
            # ceil division to ensure all nodes are assigned
            remaining_nodes_for_multi_wildcards = len(collected_nodes) - count_single_wildcards
            nodes_left_per_multi_wildcards =  0 if count_multi_wildcards==0 else math.ceil(remaining_nodes_for_multi_wildcards/count_multi_wildcards)
            multi_wildcard_nodes_left = len(collected_nodes)  - count_single_wildcards
            #collected nodes need to be distributed of the wildcard matches. first the single wildcards are assigned a node
            #then the remaining nodes are distributed to the multi wildcards
            index = 0
            for match in consecutive_matches:
                if MatchUtils.is_single_wildcard(match.key):
                    match.nodes = collected_nodes[index:index + 1]
                    index += 1
                elif MatchUtils.is_multi_wildcard(match.key):
                    number_to_assign = min(nodes_left_per_multi_wildcards, multi_wildcard_nodes_left)
                    multi_wildcard_nodes_left -= number_to_assign
                    match.nodes = collected_nodes[index:index + number_to_assign]
                    index += number_to_assign

            # for match in consecutive_matches:
            #     if MatchUtils.is_single_wildcard(match.key):
            #         match.nodes = collected_nodes[0:1]
            #         collected_nodes.remove(collected_nodes[0])
            #     elif MatchUtils.is_multi_wildcard(match.key):
            #         match.nodes = collected_nodes[0:nodes_left_per_multi_wildcards]
            #         collected_matches = collected_nodes[nodes_left_per_multi_wildcards:]
            # at this point no additional nodes should be left
            if index < len(collected_nodes):
                return False
        return True

    def _check_single_matches(self):
        """
        Checks for single matches in the keyMatches attribute.

        This method checks if any keyMatch has exactly  one node. If not the method returns False.

        Returns:
            bool: False if any keyMatch has more than one node, otherwise None.
        """
        return all(len(keyMatch.nodes) == 1 for keyMatch in self.keyMatches if MatchUtils.is_single_wildcard(keyMatch.key))
    
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
        tu_nodes = [n for n in srcNodes]# if n.is_part_of_translation_unit()]
        while newIndex < len(tu_nodes):
            target_nodes = tu_nodes[newIndex:]
            for patterns in patterns_list:
                pattern_match = MatchFinder.match_pattern(PatternMatch(target_nodes,patterns), target_nodes, patterns)
                newIndex += 1

                if pattern_match:
                    for included_node in pattern_match.collect_nodes():
                        if included_node in tu_nodes:
                            # skip all nodes that are included in the match
                            newIndex = max(tu_nodes.index(included_node)+1, newIndex)
                    yield pattern_match
                    break # only one match is needed
        #recursively include all children
        if recursive:
            for node in tu_nodes:
                yield from MatchFinder.find_all(node.get_children(), *patterns_list)

    @staticmethod
    def match_pattern(patternMatch: PatternMatch, srcNodes: list[ASTNode], patterns: list[ASTNode])-> Optional[PatternMatch]:
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
        only_wild_cards = all(MatchUtils.is_wildcard(p) for p in patterns)
        # if there are no patterns or only wildcards left and no source nodes, return the current match
        if len(patterns) == 0 or (only_wild_cards and len(srcNodes) == 0):
            if patternMatch.validate():
                return patternMatch
            return None

        if( len(srcNodes) == 0):
            return None

        srcNode = srcNodes[0]
        patternNode = patterns[0]
        if( MatchUtils.is_wildcard(patternNode)):
            wildcard_match = patternMatch.query_create(patternNode.get_name())
            if len(patterns) > 1:
                nextMatch = MatchFinder.match_pattern(patternMatch, srcNodes, patterns[1:])
                if nextMatch:                 
                    return nextMatch  
            wildcard_match.add_node(srcNode)
            return MatchFinder.match_pattern(patternMatch, srcNodes[1:], patterns)
        elif MatchUtils.is_match(srcNode, patternNode):
            # build a path that contains all nodes involved in the match
            patternMatch.query_create(MatchUtils.EXACT_MATCH).add_node(srcNode)
            if patternNode.get_children():
                if not  MatchFinder.match_pattern(patternMatch, srcNode.get_children(), patternNode.get_children()):
                    return None
            return MatchFinder.match_pattern(patternMatch, srcNodes[1:], patterns[1:])
        return None

