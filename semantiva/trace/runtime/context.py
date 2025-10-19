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

"""Trace-context helpers for propagating run-space foreign keys."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class TraceContext:
    """Per-run context used to carry trace-scoped identifiers."""

    run_space_spec_id: Optional[str] = None
    run_space_inputs_id: Optional[str] = None
    run_space_launch_id: Optional[str] = None
    run_space_attempt: Optional[int] = None

    def set_run_space_fk(
        self,
        *,
        spec_id: str,
        launch_id: str,
        attempt: int,
        inputs_id: Optional[str] = None,
    ) -> None:
        """Populate run-space identifiers for downstream trace emission."""

        self.run_space_spec_id = spec_id
        self.run_space_launch_id = launch_id
        self.run_space_attempt = attempt
        self.run_space_inputs_id = inputs_id

    def as_run_space_fk(self) -> Dict[str, Any]:
        """Return the run-space identifiers as a mapping for convenience."""

        return {
            "run_space_spec_id": self.run_space_spec_id,
            "run_space_inputs_id": self.run_space_inputs_id,
            "run_space_launch_id": self.run_space_launch_id,
            "run_space_attempt": self.run_space_attempt,
        }
