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

"""Run-space expansion (RunSpaceV1).

This module materializes a declarative *run space* specification into a
deterministic list of concrete "runs" (plain dictionaries) plus rich metadata
describing how enumeration occurred.  A **run** is a mapping of parameter/
context keys to values used when invoking a pipeline (e.g. model name,
hyper-parameters, dataset shard, output path, etc.).

Why this exists
---------------
Users often need Cartesian exploration (product) or aligned iteration (zip)
over parameter grids, optionally mixing inline literal lists with values
loaded from external tabular / semi-structured files.  The logic here provides:

1. Deterministic ordering across processes (important for reproducibility,
     caching and run indexing).
2. Early validation with descriptive errors (duplicate keys, mismatched list
     lengths, cap overflows, rename collisions, missing columns, etc.).
3. A uniform metadata contract capturing provenance (file hashes, selected /
     renamed columns, expansion sizes) to feed tracing, auditing or scheduling.

RunSpaceV1 schema (see ``semantiva.configurations.schema``)
---------------------------------------------------------
The top-level dataclass :class:`~semantiva.configurations.schema.RunSpaceV1Config`
fields:

* ``blocks: List[RunBlock]``  Each block independently expands its keys
    according to its ``mode`` (``'zip'`` or ``'product'``) then the *block level*
    results are combined using the top-level ``combine`` strategy.
* ``combine: Literal['zip','product']``  How to merge expanded blocks.
    ``product`` builds Cartesian combinations of block runs; ``zip`` aligns runs
    positionally (all blocks must then produce the same number of runs).
* ``max_runs: int``  Hard upper bound on the number of expanded final runs.
* ``dry_run: bool``  If true, callers may choose to only inspect metadata
    (this function still returns full runs; external layers decide whether to
    *execute* them).

``RunBlock`` structure:
* ``mode``  ``'zip'`` enforces equal list lengths within the block, yielding
    one run per position; ``'product'`` forms the Cartesian product across keys.
* ``context``  Inline mapping of key -> list of values.
* ``source``  Optional :class:`RunSource` loading additional columns from an
    external file. File rows can represent *runs* (``mode='zip'``) or independent
    value lists (``mode='product'``) depending on the file semantics desired.

``RunSource`` supports ``csv``, ``json``, ``yaml`` and newline-delimited ``ndjson``.
Optional transformations:
* ``select``  Restrict to a subset of columns / keys (error if any missing).
* ``rename``  Rename columns (error on collisions after rename).

Deterministic enumeration rules
-------------------------------
* Blocks are processed in the order declared.
* Within a block, *keys are iterated in sorted(key) order* to build each run.
* For ``combine='product'`` the final ordering is the Cartesian product order
    produced by :func:`itertools.product` over the per-block run lists (itself
    ordered deterministically by the rules above).
* For ``combine='zip'`` the i-th run of each block is merged (sizes must match).

Returned value
--------------
``(runs, meta)`` where:
* ``runs``  ``List[Dict[str, Any]]`` of expanded run dictionaries.
* ``meta``  ``Dict[str, Any]`` containing:
    - ``combine`` / ``max_runs`` / ``expanded_runs``.
    - ``blocks``  list with one entry per block: ``mode``, ``size``,
        ``context_keys`` and optional ``source`` details (path, hash, select,
        rename, mode, etc.).
    - ``dry_run`` (present only if spec sets it).

Error conditions (raise ``PipelineConfigurationError``):
* Unknown modes, unsupported file types.
* Missing source file.
* Mismatched lengths under any ``zip`` semantics (key level, block level or
    top-level combine).
* Duplicate keys within a block (between context and source) or across blocks.
* Missing columns requested by ``select``.
* Rename collisions or collision with already present keys.
* Cap exceeded after full expansion.

Design note: The implementation intentionally keeps state ephemeral and uses
primitive Python containers so that higher layers can trivially serialize or
further transform the enumeration results without coupling to internal classes.
"""

# Enumeration contract:
# - Blocks are combined in the order they appear in spec.blocks.
# - Within each block, context keys are iterated in sorted(key) order.
# This guarantees deterministic run ordering across processes and executions.

from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

import yaml

from semantiva.configurations.schema import RunSource, RunSpaceV1Config
from semantiva.exceptions.pipeline_exceptions import (
    PipelineConfigurationError as ConfigurationError,
    RunSpaceMaxRunsExceededError,
)


def _coerce_scalar(value: Any) -> Any:
    """Convert string values to appropriate Python types."""
    if not isinstance(value, str):
        return value

    lowered = value.strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"

    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def _load_source_file(path: Path, file_format: str) -> Dict[str, List[Any]]:
    """Load a source file into a columnar mapping.

    Normalizes heterogeneous on-disk formats into a uniform ``Dict[str, List]``
    where each key represents a logical parameter dimension.

    Semantics by type:
    * CSV  header defines column names; each row contributes one value per
      column (rows already behave like runs for ``mode='zip'``).
    * NDJSON  each non-blank line is a JSON object merged column-wise.
    * JSON / YAML  two accepted shapes:
        - List[Mapping]: treated like CSV/NDJSON rows (rows-as-runs).
        - Mapping[str, (List|scalar)]: scalars are auto-wrapped into 1-length
          lists (useful for broadcasting with other multi-valued keys).

    Returns
    -------
    Dict[str, List[Any]]  column name -> list of values.
    """
    columns: Dict[str, List[Any]]

    if file_format == "csv":
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ConfigurationError("CSV source requires a header row")

            # Strip whitespace from field names to handle "value, factor, addend" style headers
            stripped_fieldnames = [field.strip() for field in reader.fieldnames]
            columns = {field: [] for field in stripped_fieldnames}
            fieldname_map = {
                original: stripped
                for original, stripped in zip(reader.fieldnames, stripped_fieldnames)
            }

            for row in reader:
                for original_field, value in row.items():
                    field = fieldname_map[original_field]
                    columns[field].append(
                        _coerce_scalar(value) if value is not None else None
                    )
        return columns

    elif file_format == "ndjson":
        columns = {}
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, Mapping):
                    raise ConfigurationError("NDJSON source lines must be JSON objects")
                for key, value in row.items():
                    columns.setdefault(str(key), []).append(value)
        return columns

    elif file_format in ("json", "yaml"):
        if file_format == "json":
            payload = json.loads(path.read_text(encoding="utf-8"))
        else:
            try:
                payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                raise ConfigurationError(f"Failed to parse YAML source: {exc}") from exc

        if isinstance(payload, list):
            columns = {}
            for row in payload:
                if not isinstance(row, Mapping):
                    raise ConfigurationError(
                        "run_space source list entries must be mappings"
                    )
                for key, value in row.items():
                    columns.setdefault(str(key), []).append(value)
            return columns
        elif isinstance(payload, Mapping):
            return {
                str(key): [value] if not isinstance(value, list) else list(value)
                for key, value in payload.items()
            }
        else:
            raise ConfigurationError(
                f"{file_format.upper()} source must be a list of mappings or a mapping"
            )

    else:
        raise ConfigurationError(f"Unsupported run_space source format: {file_format}")


def _expand_entries(entries: Dict[str, List[Any]], mode: str) -> List[Dict[str, Any]]:
    """Expand a columnar mapping into per-run dicts.

    Parameters
    ----------
    entries: Dict[str, List[Any]]
        Mapping of key -> list of possible values (lists may be empty).
    mode: str
        'zip' or 'product'.

    Returns
    -------
    List[Dict[str, Any]]
        Concrete runs honoring deterministic key ordering.
    """
    if not entries:
        return []

    ordered_keys = sorted(entries)

    if mode == "by_position":
        lengths = [len(entries[key]) for key in ordered_keys]
        if len(set(lengths)) > 1:
            lengths_by_key = {key: len(entries[key]) for key in ordered_keys}
            raise ConfigurationError(
                f"by_position block requires identical list lengths; got {lengths_by_key}"
            )

        size = lengths[0] if lengths else 0
        return [
            {key: entries[key][index] for key in ordered_keys} for index in range(size)
        ]

    elif mode == "combinatorial":
        value_iters = [entries[key] for key in ordered_keys]
        return [
            dict(zip(ordered_keys, combo)) for combo in itertools.product(*value_iters)
        ]

    else:
        raise ConfigurationError(f"Unknown expansion mode '{mode}'")


def _load_and_process_source(
    src: RunSource, base_dir: Path
) -> Tuple[Dict[str, List[Any]], Dict[str, Any]]:
    """Load a :class:`RunSource` and apply select / rename transformations.

    Produces both the transformed columns and a metadata payload capturing
    provenance (path resolution + SHA256 digest) and the transformation
    arguments.  The digest enables higher layers to invalidate caches when a
    source file changes without re-parsing content here.
    """
    # Resolve path
    candidate = Path(src.path)
    resolved = (
        candidate if candidate.is_absolute() else (base_dir / candidate).resolve()
    )
    if not resolved.exists():
        raise ConfigurationError(f"run_space source file not found: {src.path}")

    # Load columns
    columns = _load_source_file(resolved, src.format)

    # Apply select transformation
    if src.select is not None:
        selected = {}
        missing = []
        for key in src.select:
            if key in columns:
                selected[key] = columns[key]
            else:
                missing.append(key)
        if missing:
            available = sorted(columns.keys())
            raise ConfigurationError(
                f"run_space source select missing columns: {', '.join(missing)}\n"
                f"Available columns in source: {', '.join(available)}"
            )
        columns = selected

    # Apply rename transformation
    if src.rename:
        renamed = {}
        for key, values in columns.items():
            target = src.rename.get(key, key)
            if target in renamed:
                raise ConfigurationError(
                    f"run_space source rename collision for '{key}' -> '{target}'"
                )
            renamed[target] = values
        columns = renamed

    # Generate file hash
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            if chunk:
                digest.update(chunk)

    meta = {
        "path": src.path,
        "resolved_path": str(resolved),
        "format": src.format,
        "mode": src.mode,
        "select": list(src.select or []),
        "rename": dict(src.rename),
        "sha256": digest.hexdigest(),
    }
    return columns, meta


def expand_run_space(
    spec: RunSpaceV1Config, *, cwd: str | Path = "."
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Expand a :class:`RunSpaceV1Config` into concrete runs and metadata.

    This is the primary entry point for enumerating parameter spaces.  See the
    module docstring for a detailed description of semantics.  The function is
    intentionally *pure* (aside from reading source files) and side-effect
    free—callers can safely memoize its result based on the hash of the input
    specification + referenced file digests.

    Parameters
    ----------
    spec : RunSpaceV1Config
        Declarative run space description.
    cwd : Path | str, optional
        Base directory for resolving relative source file paths (defaults to
        ``'.'``).

    Returns
    -------
    (runs, meta)
        ``runs`` is the ordered list of run dictionaries; ``meta`` is the
        metadata structure described in the module level docs.
    """
    base_dir = Path(cwd)
    all_block_runs = []
    block_meta = []
    seen_keys: set[str] = set()

    # Process each block
    for index, block in enumerate(spec.blocks):
        context_entries = {key: list(values) for key, values in block.context.items()}
        source_entries: Dict[str, List[Any]] = {}
        source_meta = None

        # Load source if present
        if block.source is not None:
            source_entries, source_meta = _load_and_process_source(
                block.source, base_dir
            )
            duplicate_keys = set(context_entries).intersection(source_entries)
            if duplicate_keys:
                raise ConfigurationError(
                    f"Duplicate context key(s) within block (context vs source): {sorted(duplicate_keys)!r}"
                )

        # Combine context and source based on block mode
        if block.mode == "by_position":
            context_runs = (
                _expand_entries(context_entries, "by_position")
                if context_entries
                else None
            )
            source_mode = block.source.mode if block.source else "by_position"
            source_runs = (
                _expand_entries(source_entries, source_mode) if source_entries else None
            )

            sizes = [
                len(runs) for runs in [context_runs, source_runs] if runs is not None
            ]
            if sizes and len(set(sizes)) != 1:
                raise ConfigurationError(
                    f"by_position block requires equal run counts between context and source; got {sizes}"
                )

            run_count = sizes[0] if sizes else 0
            block_runs = []
            for i in range(run_count):
                combined = {}
                if context_runs is not None:
                    combined.update(context_runs[i])
                if source_runs is not None:
                    combined.update(source_runs[i])
                block_runs.append(combined)

        elif block.mode == "combinatorial":
            context_runs = (
                _expand_entries(context_entries, "combinatorial")
                if context_entries
                else [{}]
            )
            source_mode = block.source.mode if block.source else "combinatorial"
            source_runs = (
                _expand_entries(source_entries, source_mode) if source_entries else [{}]
            )

            block_runs = []
            for ctx in context_runs:
                for src in source_runs:
                    merged = dict(ctx)
                    merged.update(src)
                    block_runs.append(merged)

        else:
            raise ConfigurationError(f"Unknown block mode '{block.mode}'")

        # Check for duplicate keys across blocks
        current_keys = set(context_entries) | set(source_entries)
        duplicate_keys = seen_keys.intersection(current_keys)
        if duplicate_keys:
            raise ConfigurationError(
                f"Duplicate context key(s) across blocks: {sorted(duplicate_keys)!r} (at index {index})"
            )
        seen_keys.update(current_keys)

        all_block_runs.append(block_runs)

        # Build block metadata
        block_meta_dict: Dict[str, Any] = {
            "mode": block.mode,
            "size": len(block_runs),
            "context_keys": sorted(current_keys),
        }
        if source_meta is not None:
            block_meta_dict["source"] = source_meta
        block_meta.append(block_meta_dict)

    # Combine all blocks
    if not all_block_runs:
        combined_runs: List[Dict[str, Any]] = [{}]
    elif spec.combine == "combinatorial":
        if any(len(runs) == 0 for runs in all_block_runs):
            combined_runs = []
        else:
            total = 1
            for runs in all_block_runs:
                total *= len(runs)

            if total > spec.max_runs:
                raise RunSpaceMaxRunsExceededError(
                    actual_runs=total,
                    max_runs=spec.max_runs,
                )

            combined_runs = []
            for combo in itertools.product(*all_block_runs):
                merged = {}
                for part in combo:
                    merged.update(part)
                combined_runs.append(merged)

    elif spec.combine == "by_position":
        sizes = [len(runs) for runs in all_block_runs]
        if len(set(sizes)) != 1:
            raise ConfigurationError(
                f"combine=by_position requires equal block sizes; got {sizes}"
            )

        total = sizes[0] if sizes else 0
        if total > spec.max_runs:
            raise RunSpaceMaxRunsExceededError(
                actual_runs=total,
                max_runs=spec.max_runs,
            )

        combined_runs = []
        for idx in range(total):
            merged = {}
            for runs in all_block_runs:
                merged.update(runs[idx])
            combined_runs.append(merged)

    else:
        raise ConfigurationError(f"Unknown run_space combine mode '{spec.combine}'")

    # Build final metadata
    meta: Dict[str, Any] = {
        "combine": spec.combine,
        "max_runs": spec.max_runs,
        "expanded_runs": len(combined_runs),
        "blocks": block_meta,
    }
    if spec.dry_run:
        meta["dry_run"] = True

    return combined_runs, meta


__all__ = ["expand_run_space"]
