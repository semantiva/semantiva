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
import hashlib
import importlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, NoReturn
from importlib.metadata import PackageNotFoundError, version as pkg_version

import yaml

from semantiva.configurations import parse_pipeline_config
from semantiva.configurations.schema import ExecutionConfig, TraceConfig
from semantiva.execution.fanout import expand_fanout
from semantiva.execution.orchestrator.factory import build_orchestrator
from semantiva.logger import Logger
from semantiva.registry.class_registry import ClassRegistry

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


def _parse_fanout_values_arg(value: str) -> List[Any]:
    parsed = _parse_yaml_value(value)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, str) and "," in parsed:
        return [_parse_yaml_value(part.strip()) for part in value.split(",")]
    return [parsed]


def _parse_fanout_multi_args(items: List[str]) -> Dict[str, List[Any]]:
    multi: Dict[str, List[Any]] = {}
    for item in items:
        key, value = _parse_key_value(item)
        if isinstance(value, list):
            multi[key] = value
        else:
            multi[key] = _parse_fanout_values_arg(str(value))
    return multi


def _build_fanout_args(
    index: int, values: Dict[str, Any], meta: Dict[str, Any]
) -> Dict[str, Any]:
    args_map: Dict[str, Any] = {
        "fanout.index": index,
        "fanout.mode": meta.get("mode", "none"),
        "fanout.values": values,
    }
    if "source_file" in meta:
        args_map["fanout.source_file"] = meta["source_file"]
    if "source_sha256" in meta:
        args_map["fanout.source_sha256"] = meta["source_sha256"]
    try:
        encoded = json.dumps(
            values, sort_keys=True, default=lambda obj: repr(obj)
        ).encode("utf-8")
    except TypeError:
        encoded = repr(values).encode("utf-8")
    if len(encoded) > 1024:
        args_map["fanout.values_sha256"] = hashlib.sha256(encoded).hexdigest()
    return args_map


def _build_trace_driver(trace_cfg: TraceConfig):
    if not trace_cfg.driver or trace_cfg.driver == "none":
        return None
    driver_name = trace_cfg.driver
    if driver_name == "jsonl":
        from semantiva.trace.drivers.jsonl import JSONLTrace

        detail = (
            trace_cfg.options.get("detail")
            if isinstance(trace_cfg.options, dict)
            else None
        )
        return JSONLTrace(trace_cfg.output_path, detail=detail)
    if driver_name == "pythonpath":
        if not trace_cfg.output_path:
            raise ValueError(
                "trace.output must specify module:Class when driver=pythonpath"
            )
        module_path, _, cls_name = trace_cfg.output_path.partition(":")
        if not module_path or not cls_name:
            raise ValueError(
                "trace.output must be in module:Class format for pythonpath driver"
            )
        mod = importlib.import_module(module_path)
        trace_cls = getattr(mod, cls_name)
        return trace_cls(**dict(trace_cfg.options))
    trace_cls = ClassRegistry.get_class(driver_name)
    kwargs = dict(trace_cfg.options)
    if trace_cfg.output_path and "output_path" not in kwargs:
        kwargs["output_path"] = trace_cfg.output_path
    return trace_cls(**kwargs)


def _build_execution_components(exec_cfg: ExecutionConfig):
    transport_obj = None
    if exec_cfg.transport:
        transport_cls = ClassRegistry.get_class(exec_cfg.transport)
        transport_obj = transport_cls()
    executor_obj = None
    if exec_cfg.executor:
        executor_cls = ClassRegistry.get_class(exec_cfg.executor)
        executor_obj = executor_cls()
    orchestrator = build_orchestrator(
        exec_cfg, transport=transport_obj, executor=executor_obj
    )
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
        help="Trace driver name ('jsonl', 'none', 'pythonpath', or registry class)",
    )
    run_p.add_argument(
        "--trace.output",
        dest="trace_output",
        help="Trace output path or driver spec",
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
        "--fanout.param",
        dest="fanout_param",
        help="Single-parameter fan-out target name",
    )
    run_p.add_argument(
        "--fanout.values",
        dest="fanout_values",
        help="Fan-out values (JSON list or comma-separated)",
    )
    run_p.add_argument(
        "--fanout.values-file",
        dest="fanout_values_file",
        help="Path to JSON/YAML file with fan-out values",
    )
    run_p.add_argument(
        "--fanout.multi",
        dest="fanout_multi",
        action="append",
        default=[],
        metavar="param=[...]",
        help="Multi-parameter fan-out ZIP values (repeatable)",
    )
    run_p.add_argument(
        "--fanout.multi-file",
        dest="fanout_multi_file",
        help="Path to JSON/YAML file containing mapping of multi fan-out values",
    )
    run_p.add_argument("--version", action="version", version=_get_version())

    inspect_p = sub.add_parser(
        "inspect", help="Inspect a pipeline configuration from a YAML file"
    )
    inspect_p.add_argument("pipeline", help="Path to the pipeline YAML file")
    inspect_p.add_argument(
        "--extended", action="store_true", help="Show extended inspection report"
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

    # Merge CLI execution/trace/fanout sections
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

    if any(
        [
            args.fanout_param,
            args.fanout_values,
            args.fanout_values_file,
            args.fanout_multi,
            args.fanout_multi_file,
        ]
    ):
        fanout_section = config.setdefault("fanout", {})
        if not isinstance(fanout_section, dict):
            print("Invalid config: fanout block must be a mapping", file=sys.stderr)
            return EXIT_CONFIG_ERROR
        if args.fanout_param:
            fanout_section["param"] = args.fanout_param
        if args.fanout_values:
            fanout_section["values"] = _parse_fanout_values_arg(args.fanout_values)
        if args.fanout_values_file:
            fanout_section["values_file"] = args.fanout_values_file
        if args.fanout_multi:
            multi = fanout_section.setdefault("multi", {})
            if not isinstance(multi, dict):
                print("Invalid config: fanout.multi must be a mapping", file=sys.stderr)
                return EXIT_CONFIG_ERROR
            try:
                multi.update(_parse_fanout_multi_args(args.fanout_multi))
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return EXIT_CONFIG_ERROR
        if args.fanout_multi_file:
            fanout_section["values_file"] = args.fanout_multi_file

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

    runs, fanout_meta = expand_fanout(
        pipeline_cfg.fanout,
        cwd=pipeline_cfg.base_dir or pipeline_path.parent,
    )
    if not runs:
        fanout_meta.setdefault("mode", "none")
        runs = [{}]
    run_count = len(runs)

    if args.dry_run:
        if ctx_dict and args.verbose:
            logger.debug("Ignoring --context for dry run")
        print(f"Graph: {len(pipeline.resolved_spec)} nodes.")
        print(f"Fan-out runs: {run_count}")
        print("Dry run OK (no execution performed).")
        return EXIT_SUCCESS

    try:
        for idx, run_values in enumerate(runs):
            run_context = dict(ctx_dict)
            run_context.update(run_values)
            fanout_args = _build_fanout_args(idx, dict(run_values), fanout_meta)
            pipeline.set_run_metadata({"args": fanout_args})
            initial_payload = (
                Payload(NoDataType(), ContextType(run_context)) if run_context else None
            )
            logger.info("▶️  Run %d/%d starting", idx + 1, run_count)
            start = time.time()
            result_payload = pipeline.process(initial_payload)
            duration = time.time() - start
            logger.info("✅ Run %d/%d completed in %.2fs", idx + 1, run_count, duration)
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
        return EXIT_SUCCESS
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return EXIT_INTERRUPT
    except (
        Exception
    ) as exc:  # pragma: no cover - runtime failures are tested separately
        if args.verbose:
            import traceback

            traceback.print_exc()
        else:
            print(f"Execution failed: {exc}", file=sys.stderr)
        return EXIT_RUNTIME_ERROR


def _inspect(args: argparse.Namespace) -> int:
    # Lazy imports to avoid heavy module initialization on `semantiva` import
    # Import pipeline first to avoid circular-init issues when builder pulls nodes
    from semantiva.pipeline import Pipeline as _PipelineInit  # noqa: F401
    from semantiva.registry import load_extensions
    from semantiva.inspection import (
        build_pipeline_inspection,
        extended_report,
        summary_report,
        validate_pipeline,
    )

    _configure_logger(args.verbose, args.quiet)

    config = _load_yaml(Path(args.pipeline))

    if isinstance(config, dict):
        specs = config.get("extensions")
        if not specs and isinstance(config.get("pipeline"), dict):
            specs = config["pipeline"].get("extensions")
        if specs:
            load_extensions(specs)

    # For inspection, use error-resilient builder directly
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

        invalid_lines: List[str] = []
        strict_fail = False
        for node in inspection.nodes:
            for issue in node.invalid_parameters:
                invalid_lines.append(
                    f"- node #{node.index} ({node.processor_class}): {issue['name']}"
                )
        if invalid_lines:
            print("Invalid configuration parameters:")
            for line in invalid_lines:
                print(line)
            if args.strict:
                strict_fail = True

    except Exception as exc:
        print(f"Failed to build inspection: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    report = (
        extended_report(inspection) if args.extended else summary_report(inspection)
    )
    print(report)
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
        classes += discover_from_extensions(args.extensions)
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
    # Initialize default modules at runtime to ensure core components are registered
    # for all CLI commands, while avoiding import-time circular dependencies
    from semantiva.registry.class_registry import ClassRegistry

    ClassRegistry.initialize_default_modules()

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
