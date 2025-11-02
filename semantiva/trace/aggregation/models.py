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

"""Data models for the core trace aggregator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Literal

TerminalStatus = Literal["succeeded", "error", "skipped", "cancelled"]


@dataclass
class NodeAggregate:
    """Per-node aggregation state captured while ingesting SER records."""

    node_id: str
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None
    last_seq: Optional[int] = None
    last_status: Optional[str] = None
    counts: Dict[str, int] = field(default_factory=dict)
    timing: Dict[str, Any] = field(default_factory=dict)
    last_error: Optional[Dict[str, Any]] = None


@dataclass
class RunAggregate:
    """Mutable aggregation state for a single pipeline run."""

    run_id: str
    pipeline_id: Optional[str] = None
    pipeline_spec_canonical: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    run_space_launch_id: Optional[str] = None
    run_space_attempt: Optional[int] = None
    saw_start: bool = False
    saw_end: bool = False
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None
    nodes: Dict[str, NodeAggregate] = field(default_factory=dict)


@dataclass
class RunCompleteness:
    """Deterministic completeness verdict for a run with supporting details."""

    run_id: str
    status: Literal["complete", "partial", "invalid"]
    problems: List[str]
    missing_nodes: List[str]
    orphan_nodes: List[str]
    nonterminal_nodes: List[str]
    summary: Dict[str, Any]


@dataclass
class LaunchAggregate:
    """Mutable aggregation state for a run-space launch attempt."""

    run_space_launch_id: str
    run_space_attempt: int
    run_space_spec_id: Optional[str] = None
    run_space_inputs_id: Optional[str] = None
    planned_run_count: Optional[int] = None
    input_fingerprints: Optional[List[Dict[str, Any]]] = None
    saw_start: bool = False
    saw_end: bool = False
    pipelines: Set[str] = field(default_factory=set)


@dataclass
class LaunchCompleteness:
    """Deterministic completeness verdict for a launch attempt."""

    run_space_launch_id: str
    run_space_attempt: int
    status: Literal["complete", "partial", "invalid"]
    problems: List[str]
    summary: Dict[str, Any]
