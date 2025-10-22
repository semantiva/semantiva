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

"""Launch identifier helpers for run-space execution."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import uuid
from typing import Optional


@dataclass
class RunSpaceLaunch:
    """Concrete launch identifier and attempt counter."""

    id: str
    attempt: int


class RunSpaceLaunchManager:
    """Produce deterministic launch identifiers with optional idempotency."""

    def create_launch(
        self,
        *,
        run_space_spec_id: str,
        run_space_inputs_id: Optional[str],
        provided_launch_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        attempt: int = 1,
    ) -> RunSpaceLaunch:
        """Generate a run space launch identifier using provided ID, idempotency key, or fresh UUID."""
        if provided_launch_id:
            return RunSpaceLaunch(id=provided_launch_id, attempt=attempt)

        if idempotency_key:
            basis = run_space_inputs_id or run_space_spec_id
            token = hashlib.sha256(
                b"semantiva:rsl1:"
                + basis.encode("ascii")
                + b":"
                + idempotency_key.encode("utf-8")
            ).hexdigest()
            return RunSpaceLaunch(id=token, attempt=attempt)

        identifier = self._uuid7_hex()
        return RunSpaceLaunch(id=identifier, attempt=attempt)

    def _uuid7_hex(self) -> str:
        if hasattr(uuid, "uuid7"):
            try:
                return uuid.uuid7().hex  # type: ignore[attr-defined]
            except Exception:
                pass
        return uuid.uuid4().hex
