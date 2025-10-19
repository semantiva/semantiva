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
from typing import Any, Dict, Iterable, List, Mapping, cast

import yaml

from semantiva.registry import RegistryProfile, apply_profile, load_extensions

from .schema import (
    ExecutionConfig,
    PipelineConfiguration,
    RunBlock,
    RunSource,
    RunSpaceV1Config,
    TraceConfig,
    RunBlockMode,
)


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


def _parse_run_space_block(block: Any) -> RunSpaceV1Config:
    if block is None:
        return RunSpaceV1Config()
    if not isinstance(block, Mapping):
        raise ValueError("run_space block must be a mapping if provided")

    cfg = RunSpaceV1Config()
    combine = str(block.get("combine", "combinatorial")).lower()
    if combine not in ("by_position", "combinatorial"):
        raise ValueError("run_space.combine must be 'by_position' or 'combinatorial'")
    cfg.combine = combine  # type: ignore[assignment]

    max_runs = block.get("max_runs", 1000)
    try:
        cfg.max_runs = int(max_runs)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise ValueError("run_space.max_runs must be an integer") from exc

    cfg.dry_run = bool(block.get("dry_run", False))

    blocks_raw = block.get("blocks", [])
    if blocks_raw is None:
        blocks_raw = []
    if not isinstance(blocks_raw, list):
        raise ValueError("run_space.blocks must be a list")

    for idx, entry in enumerate(blocks_raw):
        if not isinstance(entry, Mapping):
            raise ValueError(f"run_space.blocks[{idx}] must be a mapping")
        mode = str(entry.get("mode", "")).lower()
        if mode not in ("by_position", "combinatorial"):
            raise ValueError(f"run_space.blocks[{idx}] has invalid mode '{mode}'")

        context = entry.get("context") or {}
        if not isinstance(context, Mapping):
            raise ValueError(f"run_space.blocks[{idx}].context must be a mapping")
        context_map: Dict[str, List[Any]] = {}
        for key, value in context.items():
            if not isinstance(value, list):
                raise ValueError(
                    f"run_space.blocks[{idx}].context['{key}'] must be a list"
                )
            context_map[str(key)] = list(value)

        source_entry = entry.get("source")
        run_source: RunSource | None = None
        if source_entry is not None:
            if not isinstance(source_entry, Mapping):
                raise ValueError(f"run_space.blocks[{idx}].source must be a mapping")
            source_format = str(source_entry.get("format", "")).lower()
            if source_format not in ("csv", "json", "yaml", "ndjson"):
                raise ValueError(
                    f"run_space.blocks[{idx}].source.format must be one of 'csv', 'json', 'yaml', 'ndjson'"
                )
            raw_path = source_entry.get("path")
            if not isinstance(raw_path, str):
                raise ValueError(
                    f"run_space.blocks[{idx}].source.path must be a string"
                )
            select = source_entry.get("select")
            if select is not None and not isinstance(select, list):
                raise ValueError(
                    f"run_space.blocks[{idx}].source.select must be a list"
                )
            rename = source_entry.get("rename") or {}
            if not isinstance(rename, Mapping):
                raise ValueError(
                    f"run_space.blocks[{idx}].source.rename must be a mapping"
                )
            rename_dict = {str(k): str(v) for k, v in rename.items()}
            mode_override_raw = str(source_entry.get("mode", "by_position")).lower()
            if mode_override_raw not in ("by_position", "combinatorial"):
                raise ValueError(
                    f"run_space.blocks[{idx}].source.mode must be 'by_position' or 'combinatorial'"
                )
            # mypy: cast the string literal to the RunBlockMode literal type
            mode_override = cast(RunBlockMode, mode_override_raw)
            run_source = RunSource(
                format=source_format,  # type: ignore[arg-type]
                path=raw_path,
                select=list(select) if select is not None else None,
                rename=rename_dict,
                mode=mode_override,
            )

        cfg.blocks.append(RunBlock(mode=mode, context=context_map, source=run_source))  # type: ignore[arg-type]

    # Strict duplicate keys across blocks (context definitions only). Source keys
    # are validated during execution planning where files are available.
    seen_keys: set[str] = set()
    for idx, block_cfg in enumerate(cfg.blocks):
        dup = seen_keys.intersection(block_cfg.context.keys())
        if dup:
            dup_sorted = ", ".join(sorted(dup))
            raise ValueError(
                f"Duplicate context key(s) across run_space blocks: {dup_sorted} (at block {idx})"
            )
        seen_keys.update(block_cfg.context.keys())

    return cfg


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

    apply_profile(RegistryProfile())

    extensions = list(_extract_extensions(config))
    if extensions:
        load_extensions(extensions)

    nodes = config["pipeline"]["nodes"]
    if not isinstance(nodes, list) or not all(isinstance(n, Mapping) for n in nodes):
        raise ValueError("pipeline.nodes must be a list of mappings")

    execution_cfg = _parse_execution_block(config.get("execution"))
    trace_cfg = _parse_trace_block(config.get("trace"))
    run_space_block = config.get("run_space")
    if run_space_block is None and isinstance(config.get("pipeline"), Mapping):
        run_space_block = config["pipeline"].get("run_space")
    run_space_cfg = _parse_run_space_block(run_space_block)

    return PipelineConfiguration(
        [dict(node) for node in nodes],
        execution=execution_cfg,
        trace=trace_cfg,
        run_space=run_space_cfg,
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
