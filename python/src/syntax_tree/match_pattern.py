from typing import Optional
from syntax_tree.ast_node import ASTNode
from syntax_tree.match_pattern_computation import MatchPatternComputation


class MatchPattern:
    diagnose = False
    diagnose_recursive = False

    def __init__(self, match: Optional['MatchPattern']=None):
        if match is None:
            self.matchingPattern = None
            self.nodes: list[ASTNode] = []
            self.mappingSingle = {}
            self.mappingMultiple = {}
        else:
            self.matchingPattern = match.matchingPattern
            self.nodes: list[ASTNode] = match.nodes
            self.mappingSingle = dict(match.mappingSingle)
            self.mappingMultiple = dict(match.mappingMultiple)

    def get_matching_pattern(self):
        return self.matchingPattern

    def set_matching_pattern(self, matchingPattern):
        self.matchingPattern = matchingPattern

    def get_nodes(self):
        return self.nodes

    def set_nodes(self, nodes: list[ASTNode]):
        self.nodes = nodes

    def get_singles(self):
        return set(self.mappingSingle.keys())

    def get_multiples(self):
        return set(self.mappingMultiple.keys())

    def get_occurrences_of_single(self, key):
        return self.mappingSingle.get(key, [])

    def get_single_as_node(self, key, occurrence=0)->Optional[ASTNode]:
        if not key.startswith("$"):
            raise ValueError("Placeholders should start with a $ sign.")
        occurrences = self.get_occurrences_of_single(key)
        if occurrence < 0 or occurrence >= len(occurrences):
            return None
        return occurrences[occurrence]

    def get_occurrences_of_multiple(self, key: str):
        return self.mappingMultiple.get(key, [])

    def get_multiple_as_nodes(self, key: str, occurrence=0):
        if not key.startswith("$$"):
            raise ValueError("Placeholders should start with a $$ sign.")
        occurrences = self.get_occurrences_of_multiple(key)
        if occurrence < 0 or occurrence >= len(occurrences):
            return None
        return occurrences[occurrence]

    def has_single(self, key):
        return key in self.mappingSingle

    def has_multiple(self, key):
        return key in self.mappingMultiple

    def override_single(self, key, occurrences):
        self.mappingSingle[key] = occurrences

    def override_multiple(self, key, occurrences):
        self.mappingMultiple[key] = occurrences

    def get_single_as_string(self, key):
        node = self.get_single_as_node(key)
        return str(node) if node else None

    def get_single_as_string_with_default(self, key, default_value):
        return self.get_single_as_string(key) if self.has_single(key) else default_value

    def get_multiple_as_strings(self, key):
        nodes = self.get_multiple_as_nodes(key)
        return [str(node) for node in nodes] if nodes else []

    def has_equal_single_as_string(self, key1, key2):
        return self.get_single_as_string(key1) == self.get_single_as_string(key2)

    def get_nodes_as_raw_signature(self):
        nodes = self.get_nodes()
        return self._get_nodes_as_raw_signature(nodes)

    def get_single_as_raw_signature(self, key):
        node = self.get_single_as_node(key)

        return node.get_raw_signature() if node else None

    def get_multiple_as_raw_signature(self, key, separator=None):
        nodes = self.get_multiple_as_nodes(key)
        if not nodes:
            return ""
        if separator is None:
            return self._get_nodes_as_raw_signature(nodes)
        return separator.join(node.get_raw_signature() for node in nodes)

    def get_file_name(self):
        return self.get_nodes()[0].get_containing_filename()

    @staticmethod
    def match_any_full(patterns, instance, ignore_patterns: list[list[ASTNode]]=[]):
        matches = MatchPattern.match_any_full_multi(patterns, instance, ignore_patterns)
        return matches[0] if matches else None

    @staticmethod
    def match_any_full_multi(patterns, instance, ignore_patterns: list[list[ASTNode]]=[]):
        matches = []
        for pattern in patterns:
            match = MatchPattern.match_full_multi(pattern, instance, ignore_patterns)
            matches.extend(match)
        return matches

    @staticmethod
    def match_full(pattern, instance, ignore_patterns: list[list[ASTNode]]=[]):
        results = MatchPattern.match_full_multi(pattern, instance, ignore_patterns)
        return results[0] if results else None

    @staticmethod
    def match_full_multi(pattern, instance, ignore_patterns: list[list[ASTNode]]):
        result = MatchPatternComputation(ignore_patterns, True)
        result.match(pattern, instance, 0, True, True)
        return result.results

    @staticmethod
    def are_identical(n1, n2):
        return MatchPattern.are_identical_multi([n1], [n2])

    @staticmethod
    def are_identical_multi(ns1, ns2):
        result = MatchPatternComputation([], False)
        result.match(ns1, ns2, 0, True, True)
        return bool(result.results)

    @staticmethod
    def match_trivial(node):
        result = MatchPatternComputation([], True)
        result.match_trivial([node])
        return result.results[0]

    @staticmethod
    def match_prefix(pattern, instance, instance_start_index=0):
        result = MatchPatternComputation([], True)
        result.match(pattern, instance, instance_start_index, False, True)
        return result.results[0] if result.results else None

    @staticmethod
    def match_any_prefix(patterns, instance, instance_start_index=0):
        for pattern in patterns:
            match = MatchPattern.match_prefix(pattern, instance, instance_start_index)
            if match:
                return match
        return None

    @staticmethod
    def _get_nodes_as_raw_signature(nodes: list[ASTNode]):
        if not nodes:
            return ""
        begin = nodes[0].get_start_offset()
        end = nodes[-1].get_start_offset() + nodes[-1].get_length()
        return nodes[0].get_content(begin,end)