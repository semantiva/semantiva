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

"""YAML loader returning structured pipeline configuration objects."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from semantiva.registry import load_extensions
from semantiva.registry.class_registry import ClassRegistry

from .schema import ExecutionConfig, FanoutSpec, PipelineConfiguration, TraceConfig


def _ensure_mapping(name: str, value: Any) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"'{name}' block must be a mapping if provided")
    return value


def _parse_execution_block(block: Any) -> ExecutionConfig:
    data = _ensure_mapping("execution", block)
    # Enforce strict key naming: only 'options' is supported (not 'option')
    if "option" in data and "options" not in data:
        raise ValueError("execution block must use 'options' (mapping), not 'option'")
    options = data.get("options") or {}
    if options is None:
        options = {}
    if not isinstance(options, Mapping):
        raise ValueError("execution.options must be a mapping")
    return ExecutionConfig(
        orchestrator=data.get("orchestrator"),
        executor=data.get("executor"),
        transport=data.get("transport"),
        options=dict(options),
    )


def _parse_trace_block(block: Any) -> TraceConfig:
    data = _ensure_mapping("trace", block)
    # Enforce strict key naming: only 'options' is supported (not 'option')
    if "option" in data and "options" not in data:
        raise ValueError("trace block must use 'options' (mapping), not 'option'")
    options = data.get("options") or {}
    if not isinstance(options, Mapping):
        raise ValueError("trace.options must be a mapping")
    return TraceConfig(
        driver=data.get("driver"),
        output_path=data.get("output_path"),
        options=dict(options),
    )


def _parse_fanout_block(block: Any) -> FanoutSpec:
    if block is None:
        return FanoutSpec()
    if not isinstance(block, Mapping):
        raise ValueError("fanout block must be a mapping if provided")
    spec = FanoutSpec()
    if "param" in block:
        spec.param = block.get("param")
    if "values" in block:
        values = block.get("values")
        if values is not None and not isinstance(values, list):
            raise ValueError("fanout.values must be a list")
        spec.values = list(values) if values is not None else None
    if "values_file" in block:
        vf = block.get("values_file")
        if vf is not None and not isinstance(vf, str):
            raise ValueError("fanout.values_file must be a string path")
        spec.values_file = vf
    multi = block.get("multi")
    if multi is not None:
        if not isinstance(multi, Mapping):
            raise ValueError("fanout.multi must be a mapping of parameter -> list")
        spec.multi = {}
        for key, seq in multi.items():
            if not isinstance(seq, list):
                raise ValueError("fanout.multi entries must be lists")
            spec.multi[str(key)] = list(seq)
    if "mode" in block:
        spec.mode = str(block.get("mode") or "zip")
    return spec


def _extract_extensions(config: Mapping[str, Any]) -> Iterable[str]:
    top_level = config.get("extensions")
    if top_level:
        if isinstance(top_level, (list, tuple)):
            return list(top_level)
        return [top_level]
    pipeline_block = config.get("pipeline")
    if isinstance(pipeline_block, Mapping):
        nested = pipeline_block.get("extensions")
        if nested:
            if isinstance(nested, (list, tuple)):
                return list(nested)
            return [nested]
    return []


def parse_pipeline_config(
    config: Mapping[str, Any],
    *,
    source_path: str | None = None,
    base_dir: Path | None = None,
) -> PipelineConfiguration:
    """Convert a raw mapping into a :class:`PipelineConfiguration`."""

    if (
        not isinstance(config, Mapping)
        or "pipeline" not in config
        or not isinstance(config["pipeline"], Mapping)
        or "nodes" not in config["pipeline"]
    ):
        raise ValueError(
            "Invalid pipeline configuration: YAML file must contain a 'pipeline' "
            "section with a 'nodes' list."
        )

    ClassRegistry.initialize_default_modules()

    extensions = list(_extract_extensions(config))
    if extensions:
        load_extensions(extensions)

    nodes = config["pipeline"]["nodes"]
    if not isinstance(nodes, list) or not all(isinstance(n, Mapping) for n in nodes):
        raise ValueError("pipeline.nodes must be a list of mappings")

    execution_cfg = _parse_execution_block(config.get("execution"))
    trace_cfg = _parse_trace_block(config.get("trace"))
    fanout_cfg = _parse_fanout_block(config.get("fanout"))

    return PipelineConfiguration(
        [dict(node) for node in nodes],
        execution=execution_cfg,
        trace=trace_cfg,
        fanout=fanout_cfg,
        extensions=extensions,
        source_path=source_path,
        base_dir=base_dir,
        raw=dict(config),
    )


def load_pipeline_from_yaml(yaml_file: str) -> PipelineConfiguration:
    """Load a Semantiva pipeline configuration from a YAML file."""

    path = Path(yaml_file).expanduser().resolve()
    with path.open("r", encoding="utf-8") as file:
        pipeline_config = yaml.safe_load(file)

    return parse_pipeline_config(
        pipeline_config or {},
        source_path=str(path),
        base_dir=path.parent,
    )


__all__ = ["load_pipeline_from_yaml", "parse_pipeline_config"]
