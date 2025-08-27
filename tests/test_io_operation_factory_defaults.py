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

from semantiva.data_processors.io_operation_factory import _IOOperationFactory
from semantiva.examples.test_utils import FloatValueDataSource
from semantiva.data_processors.data_processors import ParameterInfo, _NO_DEFAULT


def test_io_operation_factory_exposes_defaults():
    """Ensure _IOOperationFactory exposes default parameter values from DataSource methods

    This covers the case where a DataSource._get_data method defines optional parameters
    (e.g. value: float = 42.0). The generated DataOperation wrapper must include these
    parameters in its metadata so pipeline nodes can resolve defaults.
    """

    generated = _IOOperationFactory.create_data_operation(FloatValueDataSource)

    # Metadata should include parameter info for 'value'
    meta = generated.get_metadata()
    assert "parameters" in meta, "Generated class metadata must contain 'parameters'"
    params = meta["parameters"]
    assert "value" in params, "Parameter 'value' should be present in metadata"
    assert isinstance(params["value"], ParameterInfo)

    # Default should be 42.0 (not _NO_DEFAULT)
    assert params["value"].default is not _NO_DEFAULT
    assert params["value"].default == 42.0
