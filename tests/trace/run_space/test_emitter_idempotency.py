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

from __future__ import annotations

from typing import Any, List

from semantiva.trace.runtime import Fingerprint, RunSpaceTraceEmitter


class _RecordingDriver:
    def __init__(self) -> None:
        self.starts: List[dict[str, Any]] = []
        self.ends: List[dict[str, Any]] = []

    def on_run_space_start(self, run_id: str, **payload: Any) -> None:
        payload = dict(payload)
        payload["run_id"] = run_id
        self.starts.append(payload)

    def on_run_space_end(self, run_id: str, **payload: Any) -> None:
        payload = dict(payload)
        payload["run_id"] = run_id
        self.ends.append(payload)

    # Pipeline methods unused in this test
    def on_pipeline_start(self, *args: Any, **kwargs: Any) -> None: ...

    def on_node_event(self, *args: Any, **kwargs: Any) -> None: ...

    def on_pipeline_end(self, *args: Any, **kwargs: Any) -> None: ...

    def flush(self) -> None: ...

    def close(self) -> None: ...


def test_emit_start_idempotent_within_process():
    driver = _RecordingDriver()
    emitter = RunSpaceTraceEmitter(driver)
    fp = Fingerprint(role="source", uri="file:///tmp", digest_sha256="abc")

    emitter.emit_start(
        run_space_spec_id="spec",
        run_space_launch_id="launch",
        run_space_attempt=1,
        run_space_combine_mode="combinatorial",
        run_space_total_runs=10,
        run_space_inputs_id=None,
        run_space_input_fingerprints=[fp],
    )
    emitter.emit_start(
        run_space_spec_id="spec",
        run_space_launch_id="launch",
        run_space_attempt=1,
        run_space_combine_mode="combinatorial",
        run_space_total_runs=10,
        run_space_inputs_id=None,
        run_space_input_fingerprints=[fp],
    )
    emitter.emit_start(
        run_space_spec_id="spec",
        run_space_launch_id="launch",
        run_space_attempt=2,
        run_space_combine_mode="combinatorial",
        run_space_total_runs=10,
        run_space_inputs_id=None,
        run_space_input_fingerprints=[fp],
    )

    assert len(driver.starts) == 2
    attempts = {start["run_space_attempt"] for start in driver.starts}
    assert attempts == {1, 2}

    emitter.emit_end(
        run_space_launch_id="launch",
        run_space_attempt=1,
        summary={"completed_runs": 1},
    )
    assert driver.ends[0]["summary"]["completed_runs"] == 1
