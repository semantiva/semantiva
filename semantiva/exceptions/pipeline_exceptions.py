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

"""Exception classes for pipeline construction, validation, and runtime errors.

Defines custom exception hierarchy for Semantiva pipeline operations.
"""

# Description: Custom exceptions for the semantiva package.

from typing import Dict, List


class PipelineConfigurationError(Exception):
    """Raised when the pipeline configuration is invalid."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class PipelineTopologyError(Exception):
    """Raised when the pipeline topology is invalid."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class RunSpaceMaxRunsExceededError(Exception):
    """Raised when run space expansion exceeds the configured max_runs limit."""

    def __init__(self, actual_runs: int, max_runs: int, message: str | None = None):
        self.actual_runs = actual_runs
        self.max_runs = max_runs
        if message is None:
            message = f"Run space expansion would create {actual_runs:,} runs, exceeds `max_runs` limit of {max_runs:,}"
        super().__init__(message)
        self.message = message


class InvalidNodeParameterError(ValueError):
    """Raised when a node's configuration contains unsupported parameters."""

    def __init__(
        self,
        *,
        processor_fqcn: str,
        node_uuid: str,
        invalid: Dict[str, List[str]],
    ) -> None:
        super().__init__(
            f"Invalid parameters for {processor_fqcn} (node_uuid={node_uuid}): "
            f"{', '.join(invalid.keys())}"
        )
        self.processor_fqcn = processor_fqcn
        self.node_uuid = node_uuid
        self.invalid = invalid
