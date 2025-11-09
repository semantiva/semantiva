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
"""Command line interface for Semantiva."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict
from difflib import get_close_matches
from pathlib import Path
from typing import Any, Dict, List, NoReturn
from importlib.metadata import PackageNotFoundError, version as pkg_version

import yaml

from semantiva.configurations import parse_pipeline_config
from semantiva.configurations.schema import ExecutionConfig, TraceConfig
from semantiva.exceptions.pipeline_exceptions import (
    PipelineConfigurationError,
    RunSpaceMaxRunsExceededError,
)
from semantiva.execution.component_registry import ExecutionComponentRegistry
from semantiva.execution.run_space import expand_run_space
from semantiva.execution.orchestrator.factory import build_orchestrator
from semantiva.logger import Logger
from semantiva.registry import RegistryProfile, apply_profile
from semantiva.trace.factory import build_trace_driver
from semantiva.trace.runtime import (
    RunSpaceIdentityService,
    RunSpaceLaunchManager,
    RunSpaceTraceEmitter,
    TraceContext,
)

# Exit code constants
EXIT_SUCCESS = 0
EXIT_CLI_ERROR = 1
EXIT_FILE_ERROR = 2
EXIT_CONFIG_ERROR = 3
EXIT_RUNTIME_ERROR = 4
EXIT_INTERRUPT = 5


class _ArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser that exits with code 1 on errors."""

    def error(self, message: str) -> NoReturn:  # noqa: D401 - argparse interface
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        raise SystemExit(EXIT_CLI_ERROR)


_VERSION_ASSIGNMENT_RE = re.compile(
    r"(?m)^\s*__version__\s*=\s*['\"]([^'\"]+)['\"]\s*$"
)
_VERSION_RAW_RE = re.compile(r"(?m)^\s*([0-9A-Za-z_.+-]+)\s*$")


def _parse_version_text(text: str) -> str | None:
    """Extract a version string from file contents."""

    assignment = _VERSION_ASSIGNMENT_RE.search(text)
    if assignment:
        return assignment.group(1)

    raw = _VERSION_RAW_RE.search(text)
    if raw:
        return raw.group(1)
    return None


def _get_version() -> str:
    """Return the Semantiva version using installed metadata or source fallback."""

    try:
        return pkg_version("semantiva")
    except PackageNotFoundError:  # Running from a source tree
        pass

    module_path = Path(__file__).resolve()
    for parent in module_path.parents:
        candidate = parent / "version.txt"
        if not candidate.exists():
            continue
        try:
            parsed = _parse_version_text(
                candidate.read_text(encoding="utf-8", errors="ignore")
            )
        except OSError:  # pragma: no cover - unexpected IO failure
            continue
        if parsed:
            return parsed
    return "unknown"


def _apply_override(config: Any, key: str, value: Any) -> None:
    """Apply a dotted-path override to a nested configuration object."""

    parts = key.split(".")
    target = config
    for part in parts[:-1]:
        if isinstance(target, list):
            idx = int(part)
            if idx >= len(target):
                raise KeyError(key)
            target = target[idx]
        elif isinstance(target, dict):
            if part not in target:
                raise KeyError(key)
            target = target[part]
        else:  # pragma: no cover - defensive
            raise KeyError(key)

    last = parts[-1]
    if isinstance(target, list):
        idx = int(last)
        if idx >= len(target):
            raise KeyError(key)
        target[idx] = value
    elif isinstance(target, dict):
        if last not in target:
            raise KeyError(key)
        target[last] = value
    else:  # pragma: no cover - defensive
        raise KeyError(key)


def _configure_logger(verbose: bool, quiet: bool) -> Logger:
    level = "INFO"
    if verbose:
        level = "DEBUG"
    elif quiet:
        level = "ERROR"
    return Logger(level=level)


def _parse_yaml_value(value_str: str) -> Any:
    try:
        return yaml.safe_load(value_str)
    except yaml.YAMLError:
        return value_str


def _parse_key_value(item: str) -> tuple[str, Any]:
    if "=" not in item:
        raise ValueError(f"Expected key=value format, got: {item}")
    key, value_str = item.split("=", 1)
    return key, _parse_yaml_value(value_str)


def _parse_options_list(items: List[str]) -> Dict[str, Any]:
    options: Dict[str, Any] = {}
    for item in items:
        key, value = _parse_key_value(item)
        options[key] = value
    return options


def _print_run_space_plan(meta: Dict[str, Any], runs: List[Dict[str, Any]]) -> None:
    combine = meta.get("combine", "product")
    max_runs = meta.get("max_runs")
    expanded = meta.get("expanded_runs", len(runs))

    def _oneline(value: Dict[str, Any]) -> str:
        text = json.dumps(value, separators=(",", ":"), default=str)
        return text if len(text) <= 60 else text[:57] + "…"

    print("Run Space Plan")
    print(f"  combine: {combine}")
    print(f"  max_runs: {max_runs}")
    print(f"  expanded_runs: {expanded}")
    print("  blocks:")
    for idx, block_meta in enumerate(meta.get("blocks", [])):
        keys = sorted(block_meta.get("context_keys", []))
        size = block_meta.get("size", 0)
        mode = block_meta.get("mode", "zip")
        print(f"    - #{idx}: mode={mode}, size={size}, keys={repr(keys)}")
        if "source" in block_meta:
            source_meta = block_meta["source"]
            sha = source_meta.get("sha256", "")
            sha_preview = f"(sha256 {sha[:8]}…)" if sha else ""
            print(
                "      source: {format} {path} {sha}".format(
                    format=source_meta.get("format"),
                    path=source_meta.get("path"),
                    sha=sha_preview,
                )
            )

    if not runs:
        print("  preview: none (0 runs)")
        return

    preview_limit = 2
    total = len(runs)
    print("  preview:")
    head_count = min(preview_limit, total)
    for idx in range(head_count):
        print(f"    {idx + 1}: {_oneline(runs[idx])}")
    if total > preview_limit * 2:
        print("    …")
    if total > preview_limit:
        tail_start = max(preview_limit, total - preview_limit)
        for idx in range(tail_start, total):
            print(f"    {idx + 1}: {_oneline(runs[idx])}")


def _build_trace_driver(trace_cfg: TraceConfig):
    if not trace_cfg.driver or trace_cfg.driver == "none":
        return None
    return build_trace_driver(trace_cfg)


def _suggest_component(kind: str, name: str, available: List[str]) -> str:
    matches = get_close_matches(name, available, n=3, cutoff=0.6)
    suggestion = (
        f"Unknown {kind} '{name}'. Did you mean: {', '.join(matches)}?"
        if matches
        else f"Unknown {kind} '{name}'."
    )
    return suggestion


def _resolve_registry_class(kind: str, name: str | None):
    if not name:
        return None

    registry = ExecutionComponentRegistry
    getters = {
        "orchestrator": registry.get_orchestrator,
        "executor": registry.get_executor,
        "transport": registry.get_transport,
    }
    listers = {
        "orchestrator": registry.list_orchestrators,
        "executor": registry.list_executors,
        "transport": registry.list_transports,
    }
    getter = getters[kind]
    try:
        return getter(name)
    except KeyError as exc:
        raise ValueError(_suggest_component(kind, name, listers[kind]())) from exc


def _build_execution_components(exec_cfg: ExecutionConfig):
    ExecutionComponentRegistry.initialize_defaults()

    transport_obj = None
    transport_cls = _resolve_registry_class("transport", exec_cfg.transport)
    if transport_cls is not None:
        transport_obj = transport_cls()

    executor_obj = None
    executor_cls = _resolve_registry_class("executor", exec_cfg.executor)
    if executor_cls is not None:
        executor_obj = executor_cls()

    try:
        orchestrator = build_orchestrator(
            exec_cfg, transport=transport_obj, executor=executor_obj
        )
    except ValueError as exc:
        available = ExecutionComponentRegistry.list_orchestrators()
        if exec_cfg.orchestrator:
            raise ValueError(
                _suggest_component("orchestrator", exec_cfg.orchestrator, available)
            ) from exc
        raise
    return orchestrator, transport_obj


def _load_yaml(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"File not found: {path}", file=sys.stderr)
        raise SystemExit(EXIT_FILE_ERROR) from None
    except yaml.YAMLError as exc:
        print(f"YAML error: {exc}", file=sys.stderr)
        raise SystemExit(EXIT_CONFIG_ERROR) from None


def _validate_structure(config: Any) -> List[dict[str, Any]]:
    if (
        not isinstance(config, dict)
        or "pipeline" not in config
        or not isinstance(config["pipeline"], dict)
        or "nodes" not in config["pipeline"]
    ):
        raise ValueError(
            "Invalid pipeline configuration: YAML file must contain a 'pipeline' section with a 'nodes' list."
        )
    return config["pipeline"]["nodes"]


def _parse_args(argv: List[str] | None) -> argparse.Namespace:
    parser = _ArgumentParser(prog="semantiva")
    # Top-level version flag so `semantiva --version` works as documented.
    parser.add_argument("--version", action="version", version=_get_version())
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Execute a pipeline from a YAML file")
    run_p.add_argument("pipeline", help="Path to the pipeline YAML file")
    run_p.add_argument(
        "--dry-run", action="store_true", help="Build graph without executing nodes"
    )
    run_p.add_argument(
        "--validate", action="store_true", help="Validate configuration only"
    )
    run_p.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="key=value",
        help="Override configuration values (dotted paths)",
    )
    run_p.add_argument(
        "--context",
        dest="contexts",
        action="append",
        default=[],
        metavar="key=value",
        help="Inject context key-value pairs",
    )
    run_p.add_argument(
        "-v", "--verbose", action="store_true", help="Increase log verbosity"
    )
    run_p.add_argument("-q", "--quiet", action="store_true", help="Only show errors")
    run_p.add_argument(
        "--execution.orchestrator",
        dest="exec_orchestrator",
        help="Orchestrator class name to resolve via the registry",
    )
    run_p.add_argument(
        "--execution.executor",
        dest="exec_executor",
        help="Executor class name to resolve via the registry",
    )
    run_p.add_argument(
        "--execution.transport",
        dest="exec_transport",
        help="Transport class name to resolve via the registry",
    )
    run_p.add_argument(
        "--execution.option",
        dest="exec_options",
        action="append",
        default=[],
        metavar="key=value",
        help="Additional execution option (repeatable)",
    )
    run_p.add_argument(
        "--trace.driver",
        dest="trace_driver",
        help="Trace driver name ('jsonl', default JSONL trace driver)",
    )
    run_p.add_argument(
        "--trace.output",
        dest="trace_output",
        help="Trace output path for the JSONL driver",
    )
    run_p.add_argument(
        "--trace.option",
        dest="trace_options",
        action="append",
        default=[],
        metavar="key=value",
        help="Trace driver option (repeatable)",
    )
    run_p.add_argument(
        "--run-space-file",
        dest="run_space_file",
        help="Path to a YAML file containing a run_space block",
    )
    run_p.add_argument(
        "--run-space-max-runs",
        dest="run_space_max_runs",
        type=int,
        help="Override run_space.max_runs safety limit",
    )
    run_p.add_argument(
        "--run-space-dry-run",
        dest="run_space_dry_run",
        action="store_true",
        help="Plan run_space expansions, print summary with previews, and exit",
    )
    run_p.add_argument(
        "--run-space-launch-id",
        dest="run_space_launch_id",
        help="Explicit run_space_launch_id to reuse for this execution",
    )
    run_p.add_argument(
        "--run-space-idempotency-key",
        dest="run_space_idempotency_key",
        help="Derive run_space_launch_id deterministically from spec/inputs",
    )
    run_p.add_argument(
        "--run-space-attempt",
        dest="run_space_attempt",
        type=int,
        help="Attempt counter for the run-space launch (default: 1)",
    )
    run_p.add_argument("--version", action="version", version=_get_version())

    inspect_p = sub.add_parser(
        "inspect",
        help="Inspect a pipeline configuration from a YAML file",
        description=(
            "Analyze pipeline configuration and display identity information. "
            "Shows semantic ID, config ID, run-space config ID, and required context keys. "
            "Use --extended to see per-node details including sweep parameters."
        ),
    )
    inspect_p.add_argument("pipeline", help="Path to the pipeline YAML file")
    inspect_p.add_argument(
        "--extended",
        action="store_true",
        help="Show extended report with per-node details and sweep summaries",
    )
    inspect_p.add_argument(
        "-v", "--verbose", action="store_true", help="Increase log verbosity"
    )
    inspect_p.add_argument(
        "-q", "--quiet", action="store_true", help="Only show errors"
    )
    inspect_p.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if configuration contains invalid parameters",
    )
    inspect_p.add_argument("--version", action="version", version=_get_version())

    # Developer commands
    dev_p = sub.add_parser(
        "dev",
        help="Developer tools",
        description=(
            "Developer-focused commands for Semantiva. Use 'semantiva dev lint' "
            "to run static contract checks on components."
        ),
    )
    dev_sub = dev_p.add_subparsers(dest="dev_command")

    lint_p = dev_sub.add_parser(
        "lint",
        help="Lint Semantiva components against design contracts",
        description="""
Run static contract checks for Semantiva components.

The lint command discovers components from modules, paths, extensions, or pipeline YAML
files and validates them against Semantiva's contract rules. These ensure components
follow proper design patterns, have correct method signatures and documentation, and
maintain compatibility across the Semantiva ecosystem.

Use --debug for detailed information about which rules are checked for each component.
        """.strip(),
    )
    lint_p.add_argument(
        "--modules",
        nargs="*",
        default=[],
        help="Python modules to import and validate (e.g., 'my_extension')",
    )
    lint_p.add_argument(
        "--paths",
        nargs="*",
        default=[],
        help="File system paths to scan for Python components",
    )
    lint_p.add_argument(
        "--extensions",
        nargs="*",
        default=[],
        help="Semantiva extension names to load and validate",
    )
    lint_p.add_argument(
        "--yaml",
        nargs="*",
        default=[],
        help="Pipeline YAML files to load (discovers and validates their components)",
    )
    lint_p.add_argument(
        "--export-contracts",
        default=None,
        help="Export validation rules documentation to specified Markdown file",
    )
    lint_p.add_argument(
        "--debug",
        action="store_true",
        help="Show detailed validation information: component types, applicable rules, and individual check results",
    )
    lint_p.add_argument("--version", action="version", version=_get_version())

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_usage(sys.stderr)
        raise SystemExit(EXIT_CLI_ERROR)
    if args.command == "dev" and getattr(args, "dev_command", None) is None:
        dev_p.print_usage(sys.stderr)
        raise SystemExit(EXIT_CLI_ERROR)
    return args


def _run(args: argparse.Namespace) -> int:
    from semantiva.pipeline import Pipeline, Payload
    from semantiva.context_processors import ContextType
    from semantiva.data_types import NoDataType
    from semantiva.inspection import build_pipeline_inspection, validate_pipeline

    logger = _configure_logger(args.verbose, args.quiet)

    raw_config = _load_yaml(Path(args.pipeline))
    if raw_config is None:
        config: Dict[str, Any] = {}
    elif isinstance(raw_config, dict):
        config = dict(raw_config)
    else:
        print("Invalid config: top-level YAML must be a mapping", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    for item in args.overrides:
        try:
            key, value = _parse_key_value(item)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return EXIT_CONFIG_ERROR
        try:
            _apply_override(config, key, value)
        except Exception:
            print(f"Unknown override key: {key}", file=sys.stderr)
            return EXIT_CONFIG_ERROR
    if args.verbose and args.overrides:
        logger.debug("Overrides: %s", args.overrides)

    # Merge CLI execution/trace/run_space sections
    if any(
        [
            args.exec_orchestrator,
            args.exec_executor,
            args.exec_transport,
            args.exec_options,
        ]
    ):
        exec_section = config.setdefault("execution", {})
        if not isinstance(exec_section, dict):
            print("Invalid config: execution block must be a mapping", file=sys.stderr)
            return EXIT_CONFIG_ERROR
        if args.exec_orchestrator:
            exec_section["orchestrator"] = args.exec_orchestrator
        if args.exec_executor:
            exec_section["executor"] = args.exec_executor
        if args.exec_transport:
            exec_section["transport"] = args.exec_transport
        if args.exec_options:
            opts = exec_section.setdefault("options", {})
            if not isinstance(opts, dict):
                print(
                    "Invalid config: execution.options must be a mapping",
                    file=sys.stderr,
                )
                return EXIT_CONFIG_ERROR
            try:
                opts.update(_parse_options_list(args.exec_options))
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return EXIT_CONFIG_ERROR

    if any([args.trace_driver, args.trace_output is not None, args.trace_options]):
        trace_section = config.setdefault("trace", {})
        if not isinstance(trace_section, dict):
            print("Invalid config: trace block must be a mapping", file=sys.stderr)
            return EXIT_CONFIG_ERROR
        if args.trace_driver:
            trace_section["driver"] = args.trace_driver
        if args.trace_output is not None:
            trace_section["output_path"] = args.trace_output
        if args.trace_options:
            opts = trace_section.setdefault("options", {})
            if not isinstance(opts, dict):
                print(
                    "Invalid config: trace.options must be a mapping", file=sys.stderr
                )
                return EXIT_CONFIG_ERROR
            try:
                opts.update(_parse_options_list(args.trace_options))
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return EXIT_CONFIG_ERROR

    run_space_override = False
    if args.run_space_file:
        run_space_path = Path(args.run_space_file).expanduser().resolve()
        override_payload = _load_yaml(run_space_path)
        if override_payload is None:
            run_space_block: Dict[str, Any] = {}
        elif isinstance(override_payload, dict) and "run_space" in override_payload:
            run_space_section = override_payload["run_space"]
            if not isinstance(run_space_section, dict):
                print(
                    "Invalid run-space override: run_space block must be a mapping",
                    file=sys.stderr,
                )
                return EXIT_CONFIG_ERROR
            run_space_block = dict(run_space_section)
        elif isinstance(override_payload, dict):
            run_space_block = dict(override_payload)
        else:
            print(
                "Invalid run-space override file: expected a mapping or run_space block",
                file=sys.stderr,
            )
            return EXIT_CONFIG_ERROR
        config["run_space"] = run_space_block
        run_space_override = True

    if args.run_space_max_runs is not None or args.run_space_dry_run:
        run_space_section = config.setdefault("run_space", {})
        if not isinstance(run_space_section, dict):
            print("Invalid config: run_space block must be a mapping", file=sys.stderr)
            return EXIT_CONFIG_ERROR
        if args.run_space_max_runs is not None:
            run_space_section["max_runs"] = args.run_space_max_runs
        if args.run_space_dry_run:
            run_space_section["dry_run"] = True
        run_space_override = True

    pipeline_path = Path(args.pipeline).expanduser().resolve()

    try:
        pipeline_cfg = parse_pipeline_config(
            config,
            source_path=str(pipeline_path),
            base_dir=pipeline_path.parent,
        )
    except Exception as exc:
        print(f"Invalid config: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    try:
        inspection = build_pipeline_inspection(pipeline_cfg.nodes)
        validate_pipeline(inspection)
    except Exception as exc:
        print(f"Invalid config: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    ctx_dict: Dict[str, Any] = {}
    for item in args.contexts:
        try:
            key, value = _parse_key_value(item)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return EXIT_CONFIG_ERROR
        ctx_dict[key] = value
    if args.verbose and ctx_dict:
        logger.debug("Injected context: %s", ctx_dict)

    if args.validate:
        if ctx_dict and args.verbose:
            logger.debug("Ignoring --context for validation")
        print("Config valid.")
        return EXIT_SUCCESS

    try:
        trace_driver = _build_trace_driver(pipeline_cfg.trace)
    except Exception as exc:
        print(f"Failed to build trace driver: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    try:
        orchestrator, transport_obj = _build_execution_components(
            pipeline_cfg.execution
        )
    except Exception as exc:
        print(f"Failed to build execution components: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    pipeline = Pipeline(
        pipeline_cfg.nodes,
        logger=logger,
        transport=transport_obj,
        orchestrator=orchestrator,
        trace=trace_driver,
    )

    try:
        runs, run_space_meta = expand_run_space(
            pipeline_cfg.run_space,
            cwd=pipeline_cfg.base_dir or pipeline_path.parent,
        )
    except PipelineConfigurationError as exc:
        print(f"Error: Run space configuration error\n\n{exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    except RunSpaceMaxRunsExceededError as exc:
        print(
            f"Error: {exc.message}\n\n"
            f"The run space configuration would generate {exc.actual_runs:,} runs, "
            f"which exceeds the safety limit of {exc.max_runs:,}.\n\n"
            f"To resolve this, you can:\n"
            f"  1. Reduce the size of your run space by using fewer values or 'zip' mode\n"
            f"  2. Increase the max runs with: --run-space-max-runs {exc.actual_runs}\n"
            f"  3. Preview the run space with: --run-space-dry-run\n\n"
            f"Note: Large run spaces may consume significant computational resources.",
            file=sys.stderr,
        )
        return EXIT_CONFIG_ERROR
    if run_space_override:
        run_space_meta = dict(run_space_meta)
        run_space_meta["override_source"] = "CLI"
    run_count = len(runs)

    # --- Pre-flight aggregation of missing external context keys (single check) ---
    # Use inspection.required_context_keys as the single source of truth for
    # keys that must be supplied externally (not produced by any node).
    try:
        required_external = set(
            getattr(inspection, "required_context_keys", set()) or set()
        )
    except Exception:
        required_external = set()

    probe_context: Dict[str, Any] = dict(ctx_dict)
    if runs:
        # All runs share the same context-key shape; first run is representative
        try:
            probe_context.update(runs[0])
        except Exception:
            # defensive: if runs[0] is not a mapping, ignore
            pass

    missing = sorted(required_external.difference(probe_context.keys()))
    if missing:
        msg = [
            "Error: missing required context keys:",
            *[f"  - {k}" for k in missing],
            "",
            "Provide values via one of:",
            "  * CLI:  --context key=value   (repeat for multiple)",
            "  * YAML: run_space.blocks[].context: {key: [values...]}",
            "  * Override file: --run-space-override path/to/override.yaml",
            "",
        ]
        print("\n".join(msg), file=sys.stderr)
        return EXIT_CONFIG_ERROR

    raw_cfg = pipeline_cfg.raw if isinstance(pipeline_cfg.raw, dict) else {}
    run_space_declared = False
    if isinstance(raw_cfg, dict):
        if "run_space" in raw_cfg:
            run_space_declared = True
        elif (
            isinstance(raw_cfg.get("pipeline"), dict)
            and "run_space" in raw_cfg["pipeline"]
        ):
            run_space_declared = True
    run_space_active = run_space_declared or run_space_override

    if pipeline_cfg.run_space.dry_run:
        _print_run_space_plan(run_space_meta, runs)
        print("dry_run enabled: no execution performed.")
        return EXIT_SUCCESS

    if args.dry_run:
        if ctx_dict and args.verbose:
            logger.debug("Ignoring --context for dry run")
        print(f"Graph: {len(pipeline.resolved_spec)} nodes.")
        print(f"Run space runs: {run_count}")
        if run_count:
            print(f"Combine mode: {run_space_meta.get('combine', 'product')}")
        print("Dry run OK (no execution performed).")
        return EXIT_SUCCESS

    run_space_emitter: RunSpaceTraceEmitter | None = None
    trace_context: TraceContext | None = None
    run_space_launch_id: str | None = None
    run_space_attempt = 1

    if run_space_active:
        attempt_arg = (
            args.run_space_attempt if args.run_space_attempt is not None else 1
        )
        if attempt_arg < 1:
            print("run-space attempt must be >= 1", file=sys.stderr)
            return EXIT_CONFIG_ERROR
        try:
            run_space_spec_dict = asdict(pipeline_cfg.run_space)
            base_dir = pipeline_cfg.base_dir or pipeline_path.parent
            identity_service = RunSpaceIdentityService()
            run_space_ids = identity_service.compute(
                run_space_spec_dict, base_dir=base_dir
            )
        except FileNotFoundError as exc:
            print(f"run-space source file not found: {exc}", file=sys.stderr)
            return EXIT_FILE_ERROR
        launch = RunSpaceLaunchManager().create_launch(
            run_space_spec_id=run_space_ids.spec_id,
            run_space_inputs_id=run_space_ids.inputs_id,
            provided_launch_id=args.run_space_launch_id,
            idempotency_key=args.run_space_idempotency_key,
            attempt=attempt_arg,
        )
        run_space_launch_id = launch.id
        run_space_attempt = launch.attempt
        trace_context = TraceContext()
        trace_context.set_run_space_fk(
            spec_id=run_space_ids.spec_id,
            launch_id=launch.id,
            attempt=launch.attempt,
            inputs_id=run_space_ids.inputs_id,
        )
        if trace_driver is not None:
            run_space_emitter = RunSpaceTraceEmitter(trace_driver)
            run_space_emitter.emit_start(
                run_space_spec_id=run_space_ids.spec_id,
                run_space_launch_id=launch.id,
                run_space_attempt=launch.attempt,
                run_space_combine_mode=run_space_meta.get("combine", "product"),
                run_space_total_runs=run_count,
                run_space_max_runs_limit=run_space_meta.get("max_runs"),
                run_space_inputs_id=run_space_ids.inputs_id,
                run_space_input_fingerprints=run_space_ids.fingerprints,
                run_space_planned_run_count=run_count,
            )

    exit_code = EXIT_SUCCESS
    runs_completed = 0

    try:
        for idx, run_values in enumerate(runs):
            run_context = dict(ctx_dict)
            run_context.update(run_values)

            # Only build run_space metadata when run_space is active
            metadata: Dict[str, Any] = {}
            if run_space_active:
                metadata = {
                    "trace_context": trace_context,
                    "run_space_index": idx,
                    "run_space_context": dict(run_context),
                }

            pipeline.set_run_metadata(metadata if metadata else None)
            initial_payload = (
                Payload(NoDataType(), ContextType(run_context)) if run_context else None
            )
            logger.info("▶️  Run %d/%d starting", idx + 1, run_count)
            start = time.time()
            result_payload = pipeline.process(initial_payload)
            duration = time.time() - start
            logger.info("✅ Run %d/%d completed in %.2fs", idx + 1, run_count, duration)
            runs_completed += 1
            try:
                logger.info("Output data: %s", repr(result_payload.data))
            except Exception:  # pragma: no cover - defensive
                logger.info("Output data: <unrepresentable data>")
            try:
                ctx = result_payload.context.to_dict()
                lines = ["Output context:"]
                for k, v in ctx.items():
                    try:
                        v_repr = repr(v)
                    except Exception:  # pragma: no cover - defensive
                        v_repr = "<unrepresentable>"
                    v_repr_repl = v_repr.replace("\n", " ")
                    lines.append(f"  {k}: {v_repr_repl}")
                logger.info("\n".join(lines))
            except Exception:  # pragma: no cover - defensive
                logger.info("Output context: <unrepresentable context>")
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        exit_code = EXIT_INTERRUPT
    except (
        Exception
    ) as exc:  # pragma: no cover - runtime failures are tested separately
        if args.verbose:
            import traceback

            traceback.print_exc()
        else:
            print(f"Execution failed: {exc}", file=sys.stderr)
        exit_code = EXIT_RUNTIME_ERROR
    finally:
        if run_space_emitter is not None and run_space_launch_id is not None:
            summary: dict[str, int | str] = {
                "planned_runs": run_count,
                "completed_runs": runs_completed,
            }
            if exit_code == EXIT_INTERRUPT:
                summary["status"] = "interrupted"
            elif exit_code != EXIT_SUCCESS:
                summary["status"] = "failed"
            run_space_emitter.emit_end(
                run_space_launch_id=run_space_launch_id,
                run_space_attempt=run_space_attempt,
                summary=summary,
            )

    return exit_code


def _inspect(args: argparse.Namespace) -> int:
    # Lazy imports to avoid heavy module initialization on `semantiva` import
    # Import pipeline first to avoid circular-init issues when builder pulls nodes
    from semantiva.pipeline import Pipeline as _PipelineInit  # noqa: F401
    from semantiva.registry import load_extensions
    from semantiva.inspection import (
        build,
        build_pipeline_inspection,
        validate_pipeline,
        summary_report,
    )
    from semantiva.inspection.reporter import (
        print_cli_inspection,
        _extended_report_impl,
    )

    _configure_logger(args.verbose, args.quiet)

    config = _load_yaml(Path(args.pipeline))

    if isinstance(config, dict):
        specs = config.get("extensions")
        if not specs and isinstance(config.get("pipeline"), dict):
            specs = config["pipeline"].get("extensions")
        if specs:
            try:
                load_extensions(specs)
            except RuntimeError as exc:
                print(str(exc), file=sys.stderr)
                return EXIT_CONFIG_ERROR

    # For inspection, use error-resilient builder directly
    invalid_lines: List[str] = []
    node_error_lines: List[str] = []
    strict_fail = False
    payload: Dict[str, Any] | None = None

    try:
        # Try to extract node configs, but fall back gracefully if structure is invalid
        try:
            nodes = _validate_structure(config)
        except Exception as validation_error:
            # If config structure is invalid, try to provide partial information
            print(f"Configuration structure error: {validation_error}", file=sys.stderr)
            if (
                isinstance(config, dict)
                and "pipeline" in config
                and isinstance(config["pipeline"], dict)
                and "nodes" in config["pipeline"]
            ):
                nodes = config["pipeline"]["nodes"]
            else:
                # Cannot proceed with inspection
                return EXIT_CONFIG_ERROR

        # Build inspection - this is designed to be error-resilient
        inspection = build_pipeline_inspection(nodes)

        # Only validate if requested, as inspection should work even with invalid configs
        if not getattr(args, "skip_validation", False):
            try:
                validate_pipeline(inspection)
            except Exception as validation_error:
                print(
                    f"Pipeline validation warnings: {validation_error}", file=sys.stderr
                )
                print(
                    "Proceeding with inspection despite validation issues...\n",
                    file=sys.stderr,
                )

        for node in inspection.nodes:
            for issue in node.invalid_parameters:
                invalid_lines.append(
                    f"- node #{node.index} ({node.processor_class}): {issue['name']}"
                )
            for err in node.errors:
                node_error_lines.append(f"- node #{node.index}: {err}")

        payload = build(config, inspection=inspection)

        if invalid_lines and args.strict:
            strict_fail = True

    except Exception as exc:
        print(f"Failed to build inspection: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    assert payload is not None, "Payload must be built before inspection"
    # Print identity header (always shown)
    print_cli_inspection(payload, extended=False)  # Never show Nodes section
    print()  # Add blank line between identity and structure
    # Print detailed structure based on mode
    if args.extended:
        print(_extended_report_impl(inspection, payload=payload))
    else:
        print(summary_report(inspection))
    if invalid_lines:
        print()
        print("Invalid configuration parameters:")
        for line in invalid_lines:
            print(line)
    if node_error_lines:
        print()
        print("Inspection errors detected:")
        for line in node_error_lines:
            print(line)
    return 1 if strict_fail else EXIT_SUCCESS


def _lint(args: argparse.Namespace) -> int:
    # Import locally; this is a developer-only command
    from semantiva.contracts.expectations import (
        discover_from_extensions,
        discover_from_modules,
        discover_from_paths,
        discover_from_pipeline_yaml,
        discover_from_registry,
        export_contract_catalog_markdown,
        validate_components,
    )

    # Logger is already imported at module level
    logger = Logger()

    # Set debug level if requested
    if args.debug:
        logger.set_verbose_level("DEBUG")

    classes: List[type] = []
    if args.modules:
        classes += discover_from_modules(args.modules)
    if args.paths:
        classes += discover_from_paths(args.paths)
    if args.extensions:
        try:
            classes += discover_from_extensions(args.extensions)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return EXIT_CONFIG_ERROR
    if args.yaml:
        classes += discover_from_pipeline_yaml(args.yaml)
    if not classes:
        classes = discover_from_registry()

    uniq = {f"{c.__module__}.{c.__qualname__}": c for c in classes}.values()

    # Log the components being tested
    component_names = [f"{c.__module__}.{c.__qualname__}" for c in uniq]
    logger.info(f"Testing {len(component_names)} components")
    for comp_name in sorted(component_names):
        logger.info(f"  - {comp_name}")

    # Check if debug mode is enabled
    debug_mode = args.debug
    diags = validate_components(uniq, debug_mode=debug_mode)

    by_comp: Dict[str, List[Any]] = {}
    for d in diags:
        by_comp.setdefault(d.component, []).append(d)

    # Log component test results
    if not diags:
        logger.info("All components passed validation ✓")
    else:
        # Log summary
        error_count = sum(1 for d in diags if d.severity == "error")
        warning_count = sum(1 for d in diags if d.severity == "warning")
        passed_components = set(component_names) - set(by_comp.keys())

        logger.info(
            f"Validation complete: {len(passed_components)} passed, {len(by_comp)} with issues"
        )
        if error_count > 0:
            logger.info(f"  - {error_count} errors found")
        if warning_count > 0:
            logger.info(f"  - {warning_count} warnings found")

        # Log passed components
        for comp in sorted(passed_components):
            logger.info(f"  ✓ {comp}")

        # Log failed components
        for comp in sorted(by_comp.keys()):
            error_diags = [d for d in by_comp[comp] if d.severity == "error"]
            warning_diags = [d for d in by_comp[comp] if d.severity == "warning"]
            if error_diags:
                logger.info(f"  ✗ {comp} ({len(error_diags)} errors)")
            elif warning_diags:
                logger.info(f"  ⚠ {comp} ({len(warning_diags)} warnings)")

    # Print detailed diagnostic information
    for comp, ds in sorted(by_comp.items()):
        print(f"\n{comp}")
        for d in ds:
            loc = f"{d.location[0]}:{d.location[1]}" if d.location else "<unknown>"
            print(f"  {d.severity.upper()} {d.code} @ {loc}")
            print(f"    {d.message}")

    if args.export_contracts:
        export_contract_catalog_markdown(args.export_contracts)
        print(f"\nWrote contract catalog to: {args.export_contracts}")

    # CI integration: return configuration/validation error code on any error diagnostics
    return (
        EXIT_SUCCESS
        if not any(d.severity == "error" for d in diags)
        else EXIT_CONFIG_ERROR
    )


def main(argv: List[str] | None = None) -> None:
    """Entry point for the semantiva command-line interface."""
    # Initialize default processor modules and extensions for CLI usage.
    apply_profile(RegistryProfile())

    args = _parse_args(argv)
    if args.command == "run":
        code = _run(args)
    elif args.command == "inspect":
        code = _inspect(args)
    elif args.command == "dev":
        if args.dev_command == "lint":
            code = _lint(args)
        else:
            code = EXIT_CLI_ERROR
    else:
        code = EXIT_CLI_ERROR
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
