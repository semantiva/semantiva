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
Regression tests for IO metadata generation.

Ensures DataSource, PayloadSource, DataSink, and PayloadSink emit
ParameterInfo objects with default values instead of signature strings.
"""

from collections import OrderedDict
from semantiva.data_io.data_io import DataSource, DataSink, PayloadSource, PayloadSink
from semantiva.data_processors.data_processors import ParameterInfo
from semantiva.data_types import BaseDataType
from semantiva.pipeline.payload import Payload


class MySource(DataSource):
    """Test DataSource with parameters and defaults."""

    @classmethod
    def _get_data(cls, threshold: float = 0.5, count: int = 10, name: str = "test"):
        """Get test data."""
        return {"threshold": threshold, "count": count, "name": name}

    @classmethod
    def output_data_type(cls):
        return BaseDataType


class MySink(DataSink):
    """Test DataSink with parameters and defaults."""

    @classmethod
    def _send_data(cls, data, retry: int = 3, timeout: float = 30.0):
        """Send test data."""
        pass

    @classmethod
    def input_data_type(cls):
        return BaseDataType


class MyPayloadSource(PayloadSource):
    """Test PayloadSource with parameters and defaults."""

    @classmethod
    def _get_payload(cls, batch_size: int = 100, filter_enabled: bool = True):
        """Get test payload."""
        from semantiva.data_types import NoDataType
        from semantiva.context_processors.context_types import ContextType

        return Payload(data=NoDataType(), context=ContextType())

    @classmethod
    def _injected_context_keys(cls):
        return ["batch_info", "filter_status"]

    @classmethod
    def output_data_type(cls):
        return BaseDataType


class MyPayloadSink(PayloadSink):
    """Test PayloadSink with parameters and defaults."""

    @classmethod
    def _send_payload(cls, payload, compression: str = "gzip", verify: bool = False):
        """Send test payload."""
        pass

    @classmethod
    def input_data_type(cls):
        return BaseDataType


def test_datasource_metadata_parameters_are_details():
    """Verify DataSource metadata contains ParameterInfo objects."""
    meta = MySource.get_metadata()
    params = meta.get("parameters")

    assert isinstance(params, OrderedDict), f"Expected OrderedDict, got {type(params)}"

    for name, info in params.items():
        assert isinstance(
            info, ParameterInfo
        ), f"Parameter '{name}' should be ParameterInfo, got {type(info)}"
        assert hasattr(
            info, "default"
        ), f"ParameterInfo for '{name}' missing 'default' attribute"
        assert hasattr(
            info, "annotation"
        ), f"ParameterInfo for '{name}' missing 'annotation' attribute"

    # Verify specific default values
    assert (
        params["threshold"].default == 0.5
    ), f"Expected threshold default 0.5, got {params['threshold'].default}"
    assert (
        params["count"].default == 10
    ), f"Expected count default 10, got {params['count'].default}"
    assert (
        params["name"].default == "test"
    ), f"Expected name default 'test', got {params['name'].default}"


def test_datasink_metadata_parameters_are_details():
    """Verify DataSink metadata contains ParameterInfo objects."""
    meta = MySink.get_metadata()
    params = meta.get("parameters")

    assert isinstance(params, OrderedDict), f"Expected OrderedDict, got {type(params)}"

    for name, info in params.items():
        assert isinstance(
            info, ParameterInfo
        ), f"Parameter '{name}' should be ParameterInfo, got {type(info)}"
        assert hasattr(
            info, "default"
        ), f"ParameterInfo for '{name}' missing 'default' attribute"
        assert hasattr(
            info, "annotation"
        ), f"ParameterInfo for '{name}' missing 'annotation' attribute"

    # Verify specific default values
    assert "retry" in params, "Expected 'retry' parameter in metadata"
    assert (
        params["retry"].default == 3
    ), f"Expected retry default 3, got {params['retry'].default}"
    assert (
        params["timeout"].default == 30.0
    ), f"Expected timeout default 30.0, got {params['timeout'].default}"


def test_payloadsource_metadata_parameters_are_details():
    """Verify PayloadSource metadata contains ParameterInfo objects."""
    meta = MyPayloadSource.get_metadata()
    params = meta.get("parameters")

    assert isinstance(params, OrderedDict), f"Expected OrderedDict, got {type(params)}"

    for name, info in params.items():
        assert isinstance(
            info, ParameterInfo
        ), f"Parameter '{name}' should be ParameterInfo, got {type(info)}"
        assert hasattr(
            info, "default"
        ), f"ParameterInfo for '{name}' missing 'default' attribute"
        assert hasattr(
            info, "annotation"
        ), f"ParameterInfo for '{name}' missing 'annotation' attribute"

    # Verify specific default values
    assert (
        params["batch_size"].default == 100
    ), f"Expected batch_size default 100, got {params['batch_size'].default}"
    assert (
        params["filter_enabled"].default is True
    ), f"Expected filter_enabled default True, got {params['filter_enabled'].default}"

    # Verify injected context keys are present
    assert (
        "injected_context_keys" in meta
    ), "Expected 'injected_context_keys' in metadata"
    assert meta["injected_context_keys"] == ["batch_info", "filter_status"]


def test_payloadsink_metadata_parameters_are_details():
    """Verify PayloadSink metadata contains ParameterInfo objects."""
    meta = MyPayloadSink.get_metadata()
    params = meta.get("parameters")

    assert isinstance(params, OrderedDict), f"Expected OrderedDict, got {type(params)}"

    for name, info in params.items():
        assert isinstance(
            info, ParameterInfo
        ), f"Parameter '{name}' should be ParameterInfo, got {type(info)}"
        assert hasattr(
            info, "default"
        ), f"ParameterInfo for '{name}' missing 'default' attribute"
        assert hasattr(
            info, "annotation"
        ), f"ParameterInfo for '{name}' missing 'annotation' attribute"

    # Verify specific default values
    assert (
        params["compression"].default == "gzip"
    ), f"Expected compression default 'gzip', got {params['compression'].default}"
    assert (
        params["verify"].default is False
    ), f"Expected verify default False, got {params['verify'].default}"


def test_datasource_no_parameters():
    """Verify DataSource with no parameters works correctly."""

    class SimpleSource(DataSource):
        @classmethod
        def _get_data(cls):
            return {"data": "simple"}

        @classmethod
        def output_data_type(cls):
            return BaseDataType

    meta = SimpleSource.get_metadata()
    params = meta.get("parameters")

    assert isinstance(params, OrderedDict), f"Expected OrderedDict, got {type(params)}"
    assert len(params) == 0, f"Expected no parameters, got {len(params)}"


def test_metadata_structure_consistency():
    """Verify all IO classes have consistent metadata structure."""

    for cls, expected_type in [
        (MySource, "DataSource"),
        (MySink, "DataSink"),
        (MyPayloadSource, "PayloadSource"),
        (MyPayloadSink, "PayloadSink"),
    ]:
        meta = cls.get_metadata()

        assert "component_type" in meta, f"{cls.__name__} missing 'component_type'"
        assert (
            meta["component_type"] == expected_type
        ), f"{cls.__name__} has wrong component_type"

        assert "parameters" in meta, f"{cls.__name__} missing 'parameters'"
        assert isinstance(
            meta["parameters"], OrderedDict
        ), f"{cls.__name__} parameters should be OrderedDict"


def test_parameter_annotations_preserved():
    """Verify parameter type annotations are preserved in metadata."""
    meta = MySource.get_metadata()
    params = meta.get("parameters")

    # Check that annotations contain the type information
    assert (
        "float" in params["threshold"].annotation
    ), f"Expected 'float' in annotation, got {params['threshold'].annotation}"
    assert (
        "int" in params["count"].annotation
    ), f"Expected 'int' in annotation, got {params['count'].annotation}"
    assert (
        "str" in params["name"].annotation
    ), f"Expected 'str' in annotation, got {params['name'].annotation}"
