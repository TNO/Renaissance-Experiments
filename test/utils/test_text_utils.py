import pytest
from hamcrest import assert_that, is_

from renaissance.utils.text_utils import snake_case


class TestSnakeCase:
    @pytest.mark.parametrize(
        "input_str, expected",
        [
            ("CamelCase", "camel_case"),
            ("Unit2Pytest", "unit2pytest"),
            ("SimplifyRenaissance", "simplify_renaissance"),
            ("PythonRefactoring", "python_refactoring"),
            ("already_snake", "already_snake"),
            ("A", "a"),
            ("HTMLParser", "html_parser"),
            ("TestSnakeCase", "testsnake_case"),  # TODO: Is this really the expected / desired behaviour?
        ],
    )
    def test_snake_case(self, input_str, expected):
        assert_that(snake_case(input_str), is_(expected))
