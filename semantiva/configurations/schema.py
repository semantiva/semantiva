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
from typing import Any, Dict, Iterable, List, Literal, Optional, Sequence


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


RunBlockMode = Literal["by_position", "combinatorial"]


@dataclass
class RunSource:
    """External source feeding values into a run-space block.

    Files default to *rows-as-runs* semantics (``mode='by_position'``), treating each
    row/object as one run unless ``mode`` is explicitly set to ``'combinatorial'``.
    """

    format: Literal["csv", "json", "yaml", "ndjson"]
    path: str
    select: Optional[List[str]] = None
    rename: Dict[str, str] = field(default_factory=dict)
    mode: RunBlockMode = "by_position"


@dataclass
class RunBlock:
    """Single block that expands context keys via by_position or combinatorial semantics."""

    mode: RunBlockMode
    context: Dict[str, List[Any]] = field(default_factory=dict)
    source: Optional[RunSource] = None


@dataclass
class RunSpaceV1Config:
    """Version 1 run-space configuration describing blocks and global options.

    Blocks expand deterministically: they are combined in declaration order
    and, within each block, context keys are iterated in sorted order.
    """

    combine: RunBlockMode = "combinatorial"
    max_runs: int = 1000
    dry_run: bool = False
    blocks: List[RunBlock] = field(default_factory=list)


class PipelineConfiguration(list[dict[str, Any]]):
    """List-like pipeline configuration enriched with execution metadata."""

    def __init__(
        self,
        nodes: Sequence[dict[str, Any]],
        *,
        execution: Optional[ExecutionConfig] = None,
        trace: Optional[TraceConfig] = None,
        run_space: Optional[RunSpaceV1Config] = None,
        extensions: Optional[Iterable[str]] = None,
        source_path: Optional[str] = None,
        base_dir: Optional[Path] = None,
        raw: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(nodes)
        self.execution = execution or ExecutionConfig()
        self.trace = trace or TraceConfig()
        self.run_space = run_space or RunSpaceV1Config()
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
    "RunSource",
    "RunBlock",
    "RunSpaceV1Config",
    "PipelineConfiguration",
]
