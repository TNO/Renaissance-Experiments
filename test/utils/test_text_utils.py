import pytest
from hamcrest import assert_that, is_

from renaissance.utils.text_utils import snake_case


class TestSnakeCase:
    @pytest.mark.parametrize(
        "input_str, expected",
        [
            ("A", "a"),
            ("already_snake", "already_snake"),
            ("Base64Encode", "base64_encode"),
            ("CamelCase", "camel_case"),
            ("HTML5Parser", "html5_parser"),
            ("HTMLParser", "html_parser"),
            ("Python3Refactoring", "python3_refactoring"),
            ("PythonRefactoring", "python_refactoring"),
            ("SimplifyRenaissance", "simplify_renaissance"),
            ("TestSnakeCase", "test_snake_case"),
            ("Unit2Pytest", "unit2_pytest"),
        ],
    )
    def test_snake_case(self, input_str, expected):
        assert_that(snake_case(input_str), is_(expected))
