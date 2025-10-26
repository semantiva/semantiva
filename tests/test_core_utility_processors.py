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

"""Tests for core utility processors (DataDump, CopyDataProbe).

This module tests the utility data processors and probes that are part of the
core Semantiva framework. These components provide common pipeline operations
like discarding data or passing it through for inspection.
"""


from semantiva.data_processors import DataDump, CopyDataProbe
from semantiva.data_types import BaseDataType, NoDataType


class SampleDataType(BaseDataType):
    """Sample data type for testing."""

    def validate(self, data):
        return isinstance(data, dict)


class TestDataDump:
    """Test suite for DataDump operation."""

    def test_input_type_is_base(self):
        """DataDump should accept BaseDataType as input."""
        assert DataDump.input_data_type() == BaseDataType

    def test_output_type_is_no_data(self):
        """DataDump should output NoDataType."""
        assert DataDump.output_data_type() == NoDataType

    def test_dumps_data_returns_no_data_type(self):
        """DataDump should discard input data and return NoDataType."""
        sample_data = SampleDataType({"key": "value"})
        dumper = DataDump()

        result = dumper.process(sample_data)

        assert isinstance(result, NoDataType)
        assert result.data is None

    def test_accepts_any_basedatatype_subclass(self):
        """DataDump should accept any subclass of BaseDataType."""
        # Create multiple different data types
        data1 = SampleDataType({"test": 1})
        data2 = BaseDataType("string data")

        dumper = DataDump()

        # Both should be accepted and return NoDataType
        result1 = dumper.process(data1)
        result2 = dumper.process(data2)

        assert isinstance(result1, NoDataType)
        assert isinstance(result2, NoDataType)

    def test_run_classmethod_convenience(self):
        """DataDump.run() should work as a convenience method."""
        sample_data = SampleDataType({"test": "data"})

        result = DataDump.run(sample_data)

        assert isinstance(result, NoDataType)

    def test_callable_interface(self):
        """DataDump should be callable like a function."""
        sample_data = SampleDataType({"foo": "bar"})
        dumper = DataDump()

        result = dumper(sample_data)

        assert isinstance(result, NoDataType)

    def test_metadata(self):
        """DataDump should have correct metadata."""
        metadata = DataDump._define_metadata()

        assert metadata["component_type"] == "DataOperation"
        assert metadata["input_data_type"] == "BaseDataType"
        assert metadata["output_data_type"] == "NoDataType"
        assert "parameters" in metadata

    def test_no_context_updates(self):
        """DataDump should not create any context keys."""
        assert DataDump.get_created_keys() == []
        assert DataDump.context_keys() == []


class TestCopyDataProbe:
    """Test suite for CopyDataProbe."""

    def test_input_type_is_base(self):
        """CopyDataProbe should accept BaseDataType as input."""
        assert CopyDataProbe.input_data_type() == BaseDataType

    def test_returns_input_unchanged(self):
        """CopyDataProbe should return the input data unchanged."""
        sample_data = SampleDataType({"key": "value"})
        probe = CopyDataProbe()

        result = probe.process(sample_data)

        assert result is sample_data
        assert result.data == {"key": "value"}

    def test_preserves_data_identity(self):
        """CopyDataProbe should preserve data object identity."""
        sample_data = SampleDataType({"test": [1, 2, 3]})
        probe = CopyDataProbe()

        result = probe.process(sample_data)

        # Should be the exact same object
        assert result is sample_data
        assert id(result) == id(sample_data)

    def test_accepts_any_basedatatype_subclass(self):
        """CopyDataProbe should accept any subclass of BaseDataType."""
        data1 = SampleDataType({"type": "sample"})
        data2 = BaseDataType("plain string")

        probe = CopyDataProbe()

        result1 = probe.process(data1)
        result2 = probe.process(data2)

        assert result1 is data1
        assert result2 is data2

    def test_run_classmethod_convenience(self):
        """CopyDataProbe.run() should work as a convenience method."""
        sample_data = SampleDataType({"test": "data"})

        result = CopyDataProbe.run(sample_data)

        assert result is sample_data

    def test_callable_interface(self):
        """CopyDataProbe should be callable like a function."""
        sample_data = SampleDataType({"foo": "bar"})
        probe = CopyDataProbe()

        result = probe(sample_data)

        assert result is sample_data

    def test_metadata(self):
        """CopyDataProbe should have correct metadata."""
        metadata = CopyDataProbe._define_metadata()

        assert metadata["component_type"] == "DataProbe"
        assert metadata["input_data_type"] == "BaseDataType"
        assert "parameters" in metadata

    def test_no_context_updates(self):
        """CopyDataProbe should not create any context keys."""
        assert CopyDataProbe.get_created_keys() == []


class TestUtilityProcessorsInPipeline:
    """Integration tests for utility processors in pipeline context."""

    def test_datadump_after_operation(self):
        """DataDump should successfully consume output from any operation."""
        # Simulate pipeline: SampleDataType -> DataDump -> NoDataType
        sample_data = SampleDataType({"source": "test"})
        dumper = DataDump()

        result = dumper.process(sample_data)

        assert isinstance(result, NoDataType)

    def test_copyprobe_inspection_point(self):
        """CopyDataProbe can be used as inspection point in pipeline."""
        # Simulate pipeline: Operation -> CopyDataProbe -> Next Operation
        sample_data = SampleDataType({"intermediate": "value"})
        probe = CopyDataProbe()

        # Probe returns data unchanged for next operation
        inspected = probe.process(sample_data)

        assert inspected is sample_data
        # Next operation would receive the same data
        assert inspected.data == {"intermediate": "value"}

    def test_type_compatibility_with_subclasses(self):
        """Utility processors should work with subclasses (runtime compat)."""
        # Both accept BaseDataType, should work with any subclass
        specific_data = SampleDataType({"specific": True})

        # DataDump should accept subclass
        dump_result = DataDump().process(specific_data)
        assert isinstance(dump_result, NoDataType)

        # CopyDataProbe should accept subclass
        probe_result = CopyDataProbe().process(specific_data)
        assert probe_result is specific_data


class TestInspectionCompatibility:
    """Test that inspection accepts utility processors with subclass inputs."""

    def test_specific_type_to_datadump_compatible(self):
        """Inspection should accept SpecificType -> DataDump(BaseDataType)."""
        from semantiva.inspection.validator import _is_compatible

        # SampleDataType is a subclass of BaseDataType
        # DataDump accepts BaseDataType
        # This should be compatible
        assert _is_compatible(SampleDataType, BaseDataType) is True

    def test_specific_type_to_copyprobe_compatible(self):
        """Inspection should accept SpecificType -> CopyDataProbe(BaseDataType)."""
        from semantiva.inspection.validator import _is_compatible

        # CopyDataProbe accepts BaseDataType
        # Any subclass should be compatible
        assert _is_compatible(SampleDataType, BaseDataType) is True

    def test_datadump_to_nosource_compatible(self):
        """Inspection should accept DataDump(NoDataType) as pipeline terminator."""
        from semantiva.inspection.validator import _is_compatible

        # DataDump outputs NoDataType
        # Should be compatible with operations that accept NoDataType
        assert _is_compatible(NoDataType, NoDataType) is True

    def test_incompatible_types_still_rejected(self):
        """Inspection should still reject truly incompatible types."""
        from semantiva.inspection.validator import _is_compatible

        # NoDataType -> SampleDataType should fail
        # (NoDataType is not a subclass of SampleDataType)
        assert _is_compatible(NoDataType, SampleDataType) is False
