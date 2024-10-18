from .ast_node import ASTNode
from .match_pattern import MatchPattern

class MatchPatternComputation:
    def __init__(self, ignore_patterns: list[list[ASTNode]], allow_placeholders=False):
        self.ignore_patterns = ignore_patterns
        self.allow_placeholders = allow_placeholders
        self.results = []

    def match_trivial(self, instance):
        for result in self.results:
            result.set_nodes(instance)
        return True

    def match(self, pattern: list[ASTNode], instance: list[ASTNode], instance_start_index=0, pattern_must_cover_end_of_instance=False, store_nodes=False):
        if pattern is None and instance is None:
            return True

        if pattern is None:
            if MatchPattern.diagnose and len(instance) > 0:
                self.dump_partial_match()
                print("Superfluous node in instance:")
                print(f"* Instance {type(instance)} at {self.get_location_as_string(instance[0])}: {self.as_text(instance[0])}")
            self.results.clear()
            return False

        if instance is None:
            if MatchPattern.diagnose and len(pattern) > 0:
                self.dump_partial_match()
                print("Superfluous node in pattern:")
                print(f"* Pattern {type(pattern)} at {self.get_location_as_string(pattern[0])}: {self.as_text(pattern[0])}")
            self.results.clear()
            return False

        if self.ignore_patterns is not None or instance_start_index != 0:
            instance = self.filter_ignore_patterns(instance, instance_start_index)

        placeholder_names = [self.get_placeholder_name(self.remove_placeholder_name_wrapper_layers(p, p)) if self.allow_placeholders else '' for p in pattern]

        states = [self.StateTuple(0, self.clone_computation())]
        for pattern_index in range(len(pattern)):
            next_states = []
            placeholder_name = placeholder_names[pattern_index]
            if self.is_multiple_placeholder(placeholder_name):
                for state in states:
                    for instance_index_after_multi in range(state.instance_index, len(instance) + 1):
                        next_computation = state.computation.clone_computation()
                        proposed_placeholder_length = instance_index_after_multi - state.instance_index
                        next_results = []
                        for result in next_computation.results:
                            pa = self.analyze_pattern_for_result(placeholder_names, result)

                            valid_length = True
                            earlier_mapping = result.get_multiple_as_nodes(placeholder_name)
                            if earlier_mapping is not None:
                                valid_length = proposed_placeholder_length == len(earlier_mapping)
                            else:
                                count = pa.unallocated_multi_placeholders.get(placeholder_name)
                                free_instance_positions = len(instance) - pa.allocated_positions

                                if pattern_must_cover_end_of_instance and len(pa.unallocated_multi_placeholders) == 1:
                                    valid_length = count * proposed_placeholder_length == free_instance_positions
                                else:
                                    valid_length = count * proposed_placeholder_length <= free_instance_positions

                            if valid_length:
                                multiple_placeholder_nodes = instance[state.instance_index:instance_index_after_multi]
                                if earlier_mapping is not None:
                                    local_computation = self.new_computation(self.ignore_patterns, False)
                                    old_diagnose = MatchPattern.diagnose
                                    MatchPattern.diagnose = False
                                    if local_computation.match(earlier_mapping, multiple_placeholder_nodes):
                                        occurrences = result.get_occurrences_of_multiple(placeholder_name)
                                        assert occurrences is not None
                                        occurrences.append(multiple_placeholder_nodes)
                                        result.override_multiple(placeholder_name, occurrences)
                                        next_results.append(result)
                                    MatchPattern.diagnose = old_diagnose
                                else:
                                    occurrences = [multiple_placeholder_nodes]
                                    result.override_multiple(placeholder_name, occurrences)
                                    next_results.append(result)
                        if next_results:
                            next_computation.results.clear()
                            next_computation.results.extend(next_results)
                            next_states.append(self.StateTuple(instance_index_after_multi, next_computation))
            else:
                old_diagnose = MatchPattern.diagnose
                if len(states) > 1:
                    MatchPattern.diagnose = MatchPattern.diagnose_recursive

                for state in states:
                    if state.instance_index < len(instance):
                        if state.computation.matchSingle(pattern[pattern_index], instance[state.instance_index]):
                            state.instance_index += 1
                            next_states.append(state)
                    else:
                        if MatchPattern.diagnose and len(states) == 1:
                            self.dump_partial_match()
                            print("Superfluous node in pattern:")
                            print(f"* Pattern {type(pattern[pattern_index])} at {self.get_location_as_string(pattern[pattern_index])}: {self.as_text(pattern[pattern_index])}")

                MatchPattern.diagnose = old_diagnose
            states = next_states

        self.results.clear()
        for state in states:
            if not pattern_must_cover_end_of_instance and state.instance_index > 0 or len(instance) == state.instance_index:
                if store_nodes:
                    for result in state.computation.results:
                        result.set_matching_pattern(pattern)
                        result.set_nodes(instance if len(instance) == state.instance_index else instance[:state.instance_index])
                self.results.extend(state.computation.results)
            else:
                if MatchPattern.diagnose and len(states) == 1:
                    self.dump_partial_match()
                    print("Superfluous node in instance:")
                    print(f"* Instance {type(instance[state.instance_index])} at {self.get_location_as_string(instance[state.instance_index])}: {self.as_text(instance[state.instance_index])}")
        return bool(self.results)

    class PatternAnalysis:
        def __init__(self, allocated_positions, unallocated_multi_placeholders):
            self.allocated_positions = allocated_positions
            self.unallocated_multi_placeholders = unallocated_multi_placeholders

    def analyze_pattern_for_result(self, placeholder_names: list[str], result: MatchPattern) -> PatternAnalysis:
        allocated_positions: int = 0
        unallocated_multi_placeholders: dict[str, int] = {}
        for i in range(len(placeholder_names)):
            if self.is_multiple_placeholder(placeholder_names[i]):
                nodes = result.get_multiple_as_nodes(placeholder_names[i])
                if nodes is None:
                    unallocated_multi_placeholders[placeholder_names[i]] = unallocated_multi_placeholders.get(placeholder_names[i], 0) + 1
                else:
                    allocated_positions += len(nodes)
            else:
                allocated_positions += 1
        return self.PatternAnalysis(allocated_positions, unallocated_multi_placeholders)

    def filter_ignore_patterns(self, instance, instance_start_index):
        old_diagnose = MatchPattern.diagnose
        MatchPattern.diagnose = MatchPattern.diagnose_recursive

        new_instance_nodes = []
        i = instance_start_index
        while i < len(instance):
            found = False
            if self.ignore_patterns is not None:
                for ignore_pattern in self.ignore_patterns:
                    local_computation = self.new_computation(None, self.allow_placeholders)
                    local_computation.match(ignore_pattern, instance, i, False, True)
                    if local_computation.results:
                        i += len(local_computation.results[0].get_nodes())
                        found = True
                        break
            if not found:
                new_instance_nodes.append(instance[i])
                i += 1

        MatchPattern.diagnose = old_diagnose
        return new_instance_nodes

    def matchSingle(self, pattern, instance):
        if pattern is None and instance is None:
            return True

        if pattern is None:
            if MatchPattern.diagnose:
                self.dump_partial_match()
                print("Superfluous node in instance:")
                print(f"* Instance {type(instance)} at {self.get_location_as_string(instance)}: {self.as_text(instance)}")
            self.results.clear()
            return False

        if instance is None:
            if MatchPattern.diagnose:
                self.dump_partial_match()
                print("Superfluous node in pattern:")
                print(f"* Pattern {type(pattern)} at {self.get_location_as_string(pattern)}: {self.as_text(pattern)}")
            self.results.clear()
            return False

        is_match = False
        if self.allow_placeholders:
            placeholder_name = self.get_placeholder_name(self.remove_placeholder_name_wrapper_layers(pattern, instance))

            if self.is_multiple_placeholder(placeholder_name):
                next_results = []
                for result in self.results:
                    earlier_mapping = result.get_multiple_as_nodes(placeholder_name)
                    if earlier_mapping is not None:
                        old_diagnose = MatchPattern.diagnose
                        MatchPattern.diagnose = False
                        local_computation = self.new_computation(self.ignore_patterns, False)
                        if len(earlier_mapping) == 1 and local_computation.match(earlier_mapping[0], instance):
                            occurrences = result.get_occurrences_of_multiple(placeholder_name)
                            occurrences.append([instance])
                            result.override_multiple(placeholder_name, occurrences)
                            next_results.append(result)
                        MatchPattern.diagnose = old_diagnose
                    else:
                        occurrences = [[instance]]
                        result.override_multiple(placeholder_name, occurrences)
                        next_results.append(result)
                if MatchPattern.diagnose and not next_results:
                    self.dump_partial_match()
                self.results.clear()
                self.results.extend(next_results)
                return bool(self.results)

            if self.is_single_placeholder(placeholder_name):
                is_match = self.match_single_placeholder(placeholder_name, instance)
            else:
                is_match = self.match_specific_equal_or_unequal(pattern, instance)
        else:
            is_match = self.match_specific_equal_or_unequal(pattern, instance)

        if not is_match:
            if MatchPattern.diagnose:
                if type(pattern) != type(instance):
                    print("Incompatible pattern and instance classes:")
                    print(f"* Pattern  {type(pattern)} at {self.get_location_as_string(pattern)}: {self.as_text(pattern)}")
                    print(f"* Instance {type(instance)} at {self.get_location_as_string(instance)}: {self.as_text(instance)}")
                else:
                    print(f"Incompatible pattern and instance of {type(pattern)}:")
                    print(f"* Pattern  at {self.get_location_as_string(pattern)}: {self.as_text(pattern)}")
                    print(f"* Instance at {self.get_location_as_string(instance)}: {self.as_text(instance)}")
            self.results.clear()
            return False
        else:
            return True

    def match_specific_equal_or_unequal(self, pattern, instance):
        if type(pattern) != type(instance):
            if MatchPattern.diagnose:
                self.dump_partial_match()
            self.results.clear()
            return False
        else:
            return self.match_specific(pattern, instance)

    def match_single_placeholder(self, placeholder_name, instance):
        next_results = []
        for result in self.results:
            earlier_mapping = result.get_single_as_node(placeholder_name)
            if earlier_mapping is not None:
                earlier_value = self.remove_placeholder_name_wrapper_layers(earlier_mapping, instance)
                instance_value = self.remove_placeholder_name_wrapper_layers(instance, instance)
                old_diagnose = MatchPattern.diagnose
                MatchPattern.diagnose = False
                local_match = self.new_computation(self.ignore_patterns, False)
                if local_match.match(earlier_value, instance_value):
                    occurrences = result.get_occurrences_of_single(placeholder_name)
                    replacement = []
                    for occurrence in occurrences:
                        occurrence_value = self.remove_placeholder_name_wrapper_layers(occurrence, instance)
                        new_occurrence_value = self.get_highest_matching_node(occurrence, occurrence_value, instance_value)
                        replacement.append(new_occurrence_value)
                    occurrence_value = self.remove_placeholder_name_wrapper_layers(replacement[0], instance)
                    new_instance_value = self.get_highest_matching_node(instance, instance_value, occurrence_value)
                    replacement.append(new_instance_value)
                    result.override_single(placeholder_name, replacement)
                    next_results.append(result)
                MatchPattern.diagnose = old_diagnose
            else:
                result.override_single(placeholder_name, [instance])
                next_results.append(result)
        if MatchPattern.diagnose and not next_results:
            self.dump_partial_match()
        self.results.clear()
        self.results.extend(next_results)
        return bool(self.results)

    def get_highest_matching_node(self, top_node1:ASTNode, sub_node1:ASTNode, sub_node2: ASTNode):
        while sub_node1 != top_node1:
            parent1 = sub_node1.get_parent()
            parent2 = sub_node2.get_parent()
            if parent1 and parent2 and parent1.get_kind() == parent2.get_kind:
                sub_node1 = parent1
                sub_node2 = parent2
            else:
                return sub_node1
        return sub_node1

    def dump_partial_match(self):
        print("Derived placeholder values:")
        for result in self.results:
            for single_placeholder in result.get_singles():
                l = result.get_single_as_node(single_placeholder)
                print(f"* {single_placeholder} of {type(l)}: {self.as_text(l)}")
            for multiple_placeholder in result.get_multiples():
                lst = result.get_multiple_as_nodes(multiple_placeholder)
                print(f"* {multiple_placeholder}: [{len(lst)}]")
                for l in lst:
                    print(f"  - {type(l)}: {self.as_text(l)}")
            print("  -----")

    class StateTuple:
        def __init__(self, instance_index, computation):
            self.instance_index = instance_index
            self.computation = computation

    def new_computation(self, ignore_patterns, allow_placeholders):
        return MatchPatternComputation(ignore_patterns, allow_placeholders)

    def clone_computation(self):
        return MatchPatternComputation(self.ignore_patterns, self.allow_placeholders)

    def is_single_placeholder(self, name):
        return name is not None and name.startswith("$") and not name.startswith("$$")

    def is_multiple_placeholder(self, name):
        return name is not None and name.startswith("$$")

    def get_placeholder_name(self, node:ASTNode):
        return node.get_name()

    def remove_placeholder_name_wrapper_layers(self, pattern, instance):
        return pattern

    def get_location_as_string(self, node:ASTNode):
            return f'{node.get_containing_filename()}:[{node.get_start_offset()}:{node.get_start_offset()+node.get_length()}]'

    def as_text(self, node:ASTNode):
        raw = node.get_raw_signature()
        return raw.replace("\n", "\n    ")

    def match_specific(self, pattern: ASTNode, instance: ASTNode):
        return pattern.isMatching(instance)