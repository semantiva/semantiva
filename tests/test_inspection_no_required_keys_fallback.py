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

from semantiva.inspection import build_pipeline_inspection


def test_inspection_does_not_use_processor_get_required_keys():
    # A configuration with no explicit required-keys exposure on processors
    cfg = [{"processor": "delete:obsolete"}]  # the factory defines no get_required_keys
    insp = build_pipeline_inspection(cfg)
    # Ensure required_context_keys is computed solely from param precedence
    assert hasattr(insp, "required_context_keys")
    # The 'obsolete' key should be detected as required through parameter resolution,
    # not through any deprecated get_required_keys() method
    assert insp.required_context_keys == {"obsolete"}
