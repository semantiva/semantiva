# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for safe expression evaluator."""

import pytest

from semantiva.utils.safe_eval import ExpressionEvaluator, ExpressionError


def test_valid_expression() -> None:
    ev = ExpressionEvaluator()
    fn = ev.compile("t * 2", {"t"})
    assert fn(t=3) == 6


def test_tuple_expression() -> None:
    ev = ExpressionEvaluator()
    fn = ev.compile("(t + 1, t * 2)", {"t"})
    result = fn(t=3)
    assert result == (4, 6)


def test_tuple_with_multiple_vars() -> None:
    ev = ExpressionEvaluator()
    fn = ev.compile("(x + y, x - y)", {"x", "y"})
    result = fn(x=5, y=2)
    assert result == (7, 3)


def test_type_conversion_functions() -> None:
    ev = ExpressionEvaluator()

    # Test float conversion
    fn_float = ev.compile("float(x)", {"x"})
    assert fn_float(x="3.14") == 3.14
    assert fn_float(x=42) == 42.0

    # Test int conversion
    fn_int = ev.compile("int(x)", {"x"})
    assert fn_int(x="42") == 42
    assert fn_int(x=3.14) == 3

    # Test str conversion
    fn_str = ev.compile("str(x)", {"x"})
    assert fn_str(x=42) == "42"
    assert fn_str(x=3.14) == "3.14"

    # Test bool conversion
    fn_bool = ev.compile("bool(x)", {"x"})
    assert fn_bool(x=1) is True
    assert fn_bool(x=0) is False


def test_mixed_type_conversion_and_arithmetic() -> None:
    ev = ExpressionEvaluator()
    fn = ev.compile("float(x) + int(y)", {"x", "y"})
    result = fn(x="3.5", y="2")
    assert result == 5.5


def test_unknown_variable() -> None:
    ev = ExpressionEvaluator()
    with pytest.raises(ExpressionError, match="Unknown variable 'x'"):
        ev.compile("t + x", {"t"})


def test_disallowed_call() -> None:
    ev = ExpressionEvaluator()
    with pytest.raises(ExpressionError, match="Only simple calls"):
        ev.compile("eval('1 + 1')", {"t"})


def test_comprehensive_regression_combination() -> None:
    """Test combination of tuple syntax, type conversion, and arithmetic."""
    ev = ExpressionEvaluator()

    # This tests the complete fix: tuple + type conversion + arithmetic
    fn = ev.compile(
        "(float(base) + offset * 2, int(multiplier))", {"base", "offset", "multiplier"}
    )
    result = fn(base="10.5", offset=5, multiplier="3")

    # Should be (float("10.5") + 5 * 2, int("3")) = (20.5, 3)
    assert result == (20.5, 3)
