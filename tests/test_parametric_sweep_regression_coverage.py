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

"""
Comprehensive regression tests for parametric sweep fixes.

This test suite ensures the following issues don't regress:
1. Tuple syntax support in parametric expressions
2. Type conversion function support (float, int, str, bool)
3. FromContext parameter signature inspection
4. Multiple FromContext parameters
5. Complex expression combinations
"""

import inspect
import pytest
from typing import cast

from semantiva.data_processors.parametric_sweep_factory import (
    ParametricSweepFactory,
    FromContext,
    SequenceSpec,
    RangeSpec,
)
from semantiva.examples.test_utils import FloatDataCollection, FloatDataType
from semantiva.data_io import DataSource
from semantiva.inspection import build_pipeline_inspection
from semantiva.pipeline import Pipeline
from semantiva.context_processors.context_types import ContextType
from semantiva.pipeline import Payload
from semantiva.data_types import NoDataType
from semantiva.utils.safe_eval import ExpressionEvaluator, ExpressionError


class TupleTestDataSource(DataSource):
    """Test data source that accepts tuple parameters."""

    @classmethod
    def _get_data(cls, tuple_param: tuple, single_param: float) -> FloatDataType:
        # Extract first element from tuple and add single param
        return FloatDataType(float(tuple_param[0] + single_param))

    @classmethod
    def output_data_type(cls):
        return FloatDataType


class MultiParamTestDataSource(DataSource):
    """Test data source for multiple parameter testing."""

    @classmethod
    def _get_data(cls, x: float, y: float, z: str) -> FloatDataType:
        # Combine parameters in some way
        return FloatDataType(float(x + y + len(z)))

    @classmethod
    def output_data_type(cls):
        return FloatDataType


class TestTupleSyntaxRegression:
    """Test cases to prevent regression of tuple syntax support."""

    def test_simple_tuple_expression(self):
        """Test that basic tuple expressions work in parametric expressions."""
        factory = ParametricSweepFactory()
        sweep_cls = factory.create(
            element=TupleTestDataSource,
            collection_output=FloatDataCollection,
            vars={"t": SequenceSpec([0, 1, 2])},
            parametric_expressions={
                "tuple_param": "(10 + 5 * t, 20)",
                "single_param": "5",
            },
        )

        pipeline = Pipeline([{"processor": sweep_cls}])
        payload = pipeline.process(Payload(NoDataType(), ContextType()))
        data = cast(FloatDataCollection, payload.data)

        # Expected: t=0: (10, 20) -> 10 + 5 = 15
        #          t=1: (15, 20) -> 15 + 5 = 20
        #          t=2: (20, 20) -> 20 + 5 = 25
        expected = [15.0, 20.0, 25.0]
        actual = [item.data for item in data]
        assert actual == expected

    def test_nested_tuple_expression(self):
        """Test that nested tuples work in expressions."""
        evaluator = ExpressionEvaluator()

        # Compile expression with nested tuple
        expr = evaluator.compile("((1 + x, 2), (3, 4 + y))", {"x", "y"})

        # Evaluate with variables
        result = expr(x=5, y=6)

        assert result == ((6, 2), (3, 10))

    def test_tuple_with_complex_arithmetic(self):
        """Test tuples with complex mathematical expressions."""
        evaluator = ExpressionEvaluator()

        expr = evaluator.compile("(50 + 20 * t, 30 - 10 * t ** 2)", {"t"})
        result = expr(t=2)

        # Expected: (50 + 20*2, 30 - 10*2^2) = (90, -10)
        assert result == (90, -10)

    def test_tuple_ast_node_allowed(self):
        """Test that ast.Tuple is in the allowed nodes list."""
        import ast
        from semantiva.utils.safe_eval import _SafeVisitor

        assert ast.Tuple in _SafeVisitor._ALLOWED_NODES


class TestTypeConversionRegression:
    """Test cases to prevent regression of type conversion function support."""

    def test_all_type_conversion_functions_allowed(self):
        """Test that all type conversion functions are in allowed list."""
        evaluator = ExpressionEvaluator()
        required_funcs = {"float", "int", "str", "bool"}

        # Check they're in evaluation environment
        for func_name in required_funcs:
            assert func_name in evaluator.env

    def test_float_conversion_in_expression(self):
        """Test float() function works in parametric expressions."""
        factory = ParametricSweepFactory()
        sweep_cls = factory.create(
            element=MultiParamTestDataSource,
            collection_output=FloatDataCollection,
            vars={"value": FromContext("string_values")},
            parametric_expressions={"x": "float(value)", "y": "10.5", "z": "str(42)"},
        )

        ctx = ContextType()
        ctx.set_value("string_values", ["1.5", "2.7", "3.14"])

        pipeline = Pipeline([{"processor": sweep_cls}])
        payload = pipeline.process(Payload(NoDataType(), ctx))
        data = cast(FloatDataCollection, payload.data)

        # Expected: float("1.5") + 10.5 + len("42") = 1.5 + 10.5 + 2 = 14.0
        #          float("2.7") + 10.5 + len("42") = 2.7 + 10.5 + 2 = 15.2
        #          float("3.14") + 10.5 + len("42") = 3.14 + 10.5 + 2 = 15.64
        expected = [14.0, 15.2, 15.64]
        actual = [item.data for item in data]
        assert actual == expected

    def test_int_conversion_in_expression(self):
        """Test int() function works in parametric expressions."""
        evaluator = ExpressionEvaluator()

        expr = evaluator.compile("int(x) + int(y)", {"x", "y"})
        result = expr(x="5", y="3")

        assert result == 8

    def test_bool_conversion_in_expression(self):
        """Test bool() function works in parametric expressions."""
        evaluator = ExpressionEvaluator()

        expr = evaluator.compile("bool(x) and bool(y)", {"x", "y"})
        result = expr(x="true", y=1)

        assert result is True

    def test_str_conversion_in_expression(self):
        """Test str() function works in parametric expressions."""
        evaluator = ExpressionEvaluator()

        expr = evaluator.compile("str(x) + str(y)", {"x", "y"})
        result = expr(x=42, y=3.14)

        assert result == "423.14"


class TestFromContextSignatureRegression:
    """Test cases to prevent regression of FromContext signature inspection."""

    def test_single_from_context_signature_inspection(self):
        """Test that single FromContext parameter appears in method signature."""
        factory = ParametricSweepFactory()
        sweep_cls = factory.create(
            element=MultiParamTestDataSource,
            collection_output=FloatDataCollection,
            vars={"discovered_values": FromContext("discovered_values")},
            parametric_expressions={"x": "discovered_values", "y": "10", "z": '"test"'},
        )

        # Check method signature includes FromContext parameter
        sig = inspect.signature(sweep_cls._get_data)
        param_names = list(sig.parameters.keys())

        assert "discovered_values" in param_names
        assert "kwargs" in param_names  # Should always have kwargs

    def test_multiple_from_context_signature_inspection(self):
        """Test that multiple FromContext parameters appear in method signature."""
        factory = ParametricSweepFactory()
        sweep_cls = factory.create(
            element=MultiParamTestDataSource,
            collection_output=FloatDataCollection,
            vars={
                "first_context": FromContext("first_key"),
                "second_context": FromContext("second_key"),
                "static_var": SequenceSpec([1, 2, 3]),
            },
            parametric_expressions={
                "x": "first_context",
                "y": "second_context",
                "z": '"static"',
            },
        )

        # Check method signature includes both FromContext parameters
        sig = inspect.signature(sweep_cls._get_data)
        param_names = list(sig.parameters.keys())

        assert "first_key" in param_names
        assert "second_key" in param_names
        assert "kwargs" in param_names

    def test_pipeline_inspection_detects_from_context_keys(self):
        """Test that pipeline inspection correctly detects FromContext requirements."""
        factory = ParametricSweepFactory()
        sweep_cls = factory.create(
            element=MultiParamTestDataSource,
            collection_output=FloatDataCollection,
            vars={
                "context_val1": FromContext("required_key1"),
                "context_val2": FromContext("required_key2"),
            },
            parametric_expressions={
                "x": "context_val1",
                "y": "context_val2",
                "z": '"test"',
            },
        )

        # Build pipeline inspection
        config = [{"processor": sweep_cls}]
        inspection = build_pipeline_inspection(config)

        # Should detect both required context keys
        assert "required_key1" in inspection.required_context_keys
        assert "required_key2" in inspection.required_context_keys

    def test_no_from_context_empty_signature(self):
        """Test that processors without FromContext have minimal signature."""
        factory = ParametricSweepFactory()
        sweep_cls = factory.create(
            element=MultiParamTestDataSource,
            collection_output=FloatDataCollection,
            vars={"t": SequenceSpec([1, 2, 3])},
            parametric_expressions={"x": "t", "y": "5", "z": '"test"'},
        )

        # Check method signature only has kwargs (no FromContext params)
        sig = inspect.signature(sweep_cls._get_data)
        param_names = list(sig.parameters.keys())

        assert param_names == ["kwargs"]  # Only kwargs, no FromContext params

    def test_signature_attribute_exists(self):
        """Test that __signature__ attribute is properly attached."""
        factory = ParametricSweepFactory()
        sweep_cls = factory.create(
            element=MultiParamTestDataSource,
            collection_output=FloatDataCollection,
            vars={"context_var": FromContext("test_key")},
            parametric_expressions={"x": "context_var", "y": "1", "z": '"test"'},
        )

        # Should have __signature__ attribute
        assert hasattr(sweep_cls._get_data, "__signature__")

        # Should be an inspect.Signature instance
        assert isinstance(sweep_cls._get_data.__signature__, inspect.Signature)


class TestComplexScenarioRegression:
    """Test cases for complex combinations that could break."""

    def test_tuple_with_from_context_and_type_conversion(self):
        """Test combining tuples, FromContext, and type conversion."""
        factory = ParametricSweepFactory()
        sweep_cls = factory.create(
            element=TupleTestDataSource,
            collection_output=FloatDataCollection,
            vars={
                "base_values": FromContext("base_values"),
                "multiplier": SequenceSpec([1, 2, 3]),
            },
            parametric_expressions={
                "tuple_param": "(float(base_values) + 10 * multiplier, 20)",
                "single_param": "int(multiplier) * 2",
            },
            mode="zip",
        )

        ctx = ContextType()
        ctx.set_value("base_values", ["5.5", "10.3", "15.7"])

        pipeline = Pipeline([{"processor": sweep_cls}])
        payload = pipeline.process(Payload(NoDataType(), ctx))
        data = cast(FloatDataCollection, payload.data)

        # Expected calculations:
        # multiplier=1: tuple=(float("5.5") + 10*1, 20)=(15.5, 20), single=int(1)*2=2 -> 15.5 + 2 = 17.5
        # multiplier=2: tuple=(float("10.3") + 10*2, 20)=(30.3, 20), single=int(2)*2=4 -> 30.3 + 4 = 34.3
        # multiplier=3: tuple=(float("15.7") + 10*3, 20)=(45.7, 20), single=int(3)*2=6 -> 45.7 + 6 = 51.7
        expected = [17.5, 34.3, 51.7]
        actual = [item.data for item in data]
        assert actual == expected

    def test_pipeline_inspection_with_complex_scenario(self):
        """Test pipeline inspection works with complex parametric expressions."""
        factory = ParametricSweepFactory()
        sweep_cls = factory.create(
            element=TupleTestDataSource,
            collection_output=FloatDataCollection,
            vars={
                "context_floats": FromContext("float_data"),
                "context_strings": FromContext("string_data"),
                "range_var": RangeSpec(0, 10, steps=5),
            },
            parametric_expressions={
                "tuple_param": "(float(context_strings) + context_floats * range_var, int(range_var))",
                "single_param": "bool(range_var) and True",
            },
        )

        # Test signature inspection
        sig = inspect.signature(sweep_cls._get_data)
        param_names = set(sig.parameters.keys())

        assert "float_data" in param_names
        assert "string_data" in param_names
        assert "kwargs" in param_names

        # Test pipeline inspection
        config = [{"processor": sweep_cls}]
        inspection = build_pipeline_inspection(config)

        assert "float_data" in inspection.required_context_keys
        assert "string_data" in inspection.required_context_keys

    def test_expression_compilation_error_handling(self):
        """Test that invalid expressions still raise appropriate errors."""
        evaluator = ExpressionEvaluator()

        # Test that invalid syntax raises proper errors
        with pytest.raises(ExpressionError, match="Invalid expression syntax"):
            evaluator.compile("import os", set())

        # Test that forbidden function calls are rejected
        with pytest.raises(ExpressionError, match="Only simple calls"):
            evaluator.compile("exec('print(1)')", set())

        # Test that undefined variables raise errors
        with pytest.raises(ExpressionError, match="Unknown variable"):
            evaluator.compile("undefined_variable", set())

    def test_yaml_example_from_context_validation(self):
        """Test that the from_context_sweep_demo.yaml example validates correctly."""
        # This ensures the fixes to the example file don't regress
        from semantiva.configurations.load_pipeline_from_yaml import (
            load_pipeline_from_yaml,
        )
        import tempfile
        import os

        yaml_content = """
extensions: ["semantiva"]

pipeline:
  nodes:
    - processor: "sweep:FloatValueDataSource:FloatDataCollection"
      parameters:
        vars:
          input_value: { from_context: discovered_values }
        parametric_expressions:
          value: "float(input_value)"
"""

        # Write to temporary file and test loading
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Should load without validation errors
            config = load_pipeline_from_yaml(temp_path)
            assert len(config) == 1
            assert "processor" in config[0]
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
