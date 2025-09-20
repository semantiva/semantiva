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

"""Trace model for Step Evidence Record (SER v0 - draft).

This module defines the dataclasses used by the tracing subsystem. The Step
Evidence Record (SER) is a single record emitted for each completed pipeline
step. Drivers switch on the ``type`` field and ignore unknown fields for
forward compatibility. Version ``0`` is the draft schema used during
pre-release development.

The exhaustive description of SER fields and semantics lives in
docs/source/ser.rst.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Literal

from semantiva.pipeline.payload import Payload


Result = Literal["PASS", "FAIL", "WARN"]


@dataclass
class Check:
    """Result of a single check performed for a node."""

    code: str
    result: Result
    details: Optional[Dict[str, Any]] = None


@dataclass
class UpstreamEvidence:
    """Evidence of an upstream node's state when determining why a node ran."""

    node_id: str
    state: str
    digest: Optional[str] = None


@dataclass
class IODelta:
    """Input/output delta for a node execution."""

    read: List[str]
    created: List[str]
    updated: List[str]
    summaries: Dict[str, Dict[str, Any]]


@dataclass
class SERRecord:
    """Step Evidence Record emitted for each executed pipeline node."""

    type: Literal["ser"]
    schema_version: int
    ids: Dict[str, str]
    topology: Dict[str, List[str]]
    action: Dict[str, Any]
    io_delta: IODelta
    checks: Dict[str, Any]
    timing: Dict[str, Any]
    status: Literal["completed", "error"]
    error: Optional[Dict[str, Any]] = None
    labels: Optional[Dict[str, Any]] = None
    summaries: Optional[Dict[str, Any]] = None


class TraceDriver(Protocol):
    """Driver API for Semantiva tracing using SER records."""

    def on_pipeline_start(
        self,
        pipeline_id: str,
        run_id: str,
        canonical_spec: dict,
        meta: dict,
        pipeline_input: Optional[Payload] = None,
    ) -> None:
        """Emit a ``pipeline_start`` record."""

    def on_node_event(self, event: SERRecord) -> None:
        """Emit a single SER record for a completed node."""

    def on_pipeline_end(self, run_id: str, summary: dict) -> None:
        """Emit a ``pipeline_end`` record summarising the run."""

    def flush(self) -> None:
        """Flush any internal buffers."""

    def close(self) -> None:
        """Release resources and close the driver."""
