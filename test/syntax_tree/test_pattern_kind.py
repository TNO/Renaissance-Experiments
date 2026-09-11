from renaissance.syntax_tree.pattern_kind import PatternKind


def test_pattern_kind_values_are_distinct():
    assert PatternKind.MATCH_ONE != PatternKind.MATCH_ALL
