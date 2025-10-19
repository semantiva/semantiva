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

from semantiva.trace.runtime import RunSpaceLaunchManager


def test_launch_id_deterministic_with_idempotency_key():
    manager = RunSpaceLaunchManager()
    one = manager.create_launch(
        run_space_spec_id="spec",
        run_space_inputs_id="inputs",
        idempotency_key="abc",
    )
    two = manager.create_launch(
        run_space_spec_id="spec",
        run_space_inputs_id="inputs",
        idempotency_key="abc",
    )
    assert one.id == two.id
    assert one.attempt == two.attempt == 1


def test_launch_id_differs_when_inputs_change():
    manager = RunSpaceLaunchManager()
    first = manager.create_launch(
        run_space_spec_id="spec",
        run_space_inputs_id="inputs-a",
        idempotency_key="abc",
    )
    second = manager.create_launch(
        run_space_spec_id="spec",
        run_space_inputs_id="inputs-b",
        idempotency_key="abc",
    )
    assert first.id != second.id
