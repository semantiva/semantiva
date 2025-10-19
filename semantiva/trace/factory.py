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

"""Factory helpers for building trace drivers."""

from __future__ import annotations

from typing import Any

from semantiva.configurations.schema import TraceConfig


def build_trace_driver(trace_cfg: TraceConfig):
    """Instantiate the configured trace driver."""

    name = trace_cfg.driver or "jsonl"
    options: dict[str, Any] = dict(trace_cfg.options)
    if trace_cfg.output_path and "output_path" not in options:
        options["output_path"] = trace_cfg.output_path

    if name == "jsonl":
        from semantiva.trace.drivers.jsonl import JsonlTraceDriver

        return JsonlTraceDriver(**options)
    raise ValueError(f"Unknown trace driver {name!r}; use 'jsonl' instead.")
