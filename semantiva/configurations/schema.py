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
"""Structured configuration objects for YAML and CLI entry points."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


@dataclass
class ExecutionConfig:
    """Configuration for orchestrator, executor, and transport resolution."""

    orchestrator: Optional[str] = None
    executor: Optional[str] = None
    transport: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceConfig:
    """Configuration for trace driver construction."""

    driver: Optional[str] = None
    output_path: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FanoutSpec:
    """Declarative fan-out specification supporting single and multi-zip modes."""

    param: Optional[str] = None
    values: Optional[List[Any]] = None
    values_file: Optional[str] = None
    multi: Dict[str, List[Any]] = field(default_factory=dict)
    mode: str = "zip"


class PipelineConfiguration(list[dict[str, Any]]):
    """List-like pipeline configuration enriched with execution metadata."""

    def __init__(
        self,
        nodes: Sequence[dict[str, Any]],
        *,
        execution: Optional[ExecutionConfig] = None,
        trace: Optional[TraceConfig] = None,
        fanout: Optional[FanoutSpec] = None,
        extensions: Optional[Iterable[str]] = None,
        source_path: Optional[str] = None,
        base_dir: Optional[Path] = None,
        raw: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(nodes)
        self.execution = execution or ExecutionConfig()
        self.trace = trace or TraceConfig()
        self.fanout = fanout or FanoutSpec()
        self.extensions = tuple(extensions or ())
        self.source_path = source_path
        self.base_dir = Path(base_dir) if base_dir is not None else None
        self.raw = dict(raw or {})

    @property
    def nodes(self) -> List[dict[str, Any]]:
        """Return the pipeline nodes as a list for ergonomic access."""

        return list(self)


__all__ = [
    "ExecutionConfig",
    "TraceConfig",
    "FanoutSpec",
    "PipelineConfiguration",
]
