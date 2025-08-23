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
import sys
import time
from pathlib import Path
from typing import Any, List, NoReturn
import importlib

import yaml

from semantiva.context_processors import ContextType
from semantiva.data_types import NoDataType
from semantiva.logger import Logger
from semantiva.registry import load_extensions
from semantiva.inspection import (
    build_pipeline_inspection,
    extended_report,
    summary_report,
    validate_pipeline,
)
from semantiva.pipeline import Pipeline, Payload
from semantiva.trace.drivers.jsonl import JSONLTrace

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


def _get_version() -> str:
    """Return the package version from version.txt."""

    version_file = Path(__file__).resolve().parents[1] / "version.txt"
    try:
        namespace: dict[str, str] = {}
        exec(version_file.read_text(), namespace)  # pylint: disable=exec-used
        return namespace.get("__version__", "unknown")
    except Exception:  # pragma: no cover - fallback path
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
        "--trace-driver",
        choices=["none", "jsonl", "pythonpath"],
        default="none",
        help="Tracing driver to use",
    )
    run_p.add_argument(
        "--trace-output",
        default=None,
        help="Trace output path or driver spec",
    )
    run_p.add_argument(
        "--trace-detail",
        default="timings",
        help=("Comma-separated trace detail flags: timings, hash, repr, context, all"),
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
    inspect_p.add_argument("--version", action="version", version=_get_version())

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_usage(sys.stderr)
        raise SystemExit(EXIT_CLI_ERROR)
    return args


def _run(args: argparse.Namespace) -> int:
    logger = _configure_logger(args.verbose, args.quiet)

    config = _load_yaml(Path(args.pipeline))

    # Load extensions if specified
    if isinstance(config, dict):
        specs = config.get("extensions")
        if not specs and isinstance(config.get("pipeline"), dict):
            specs = config["pipeline"].get("extensions")
        if specs:
            load_extensions(specs)

    # Apply overrides
    for item in args.overrides:
        if "=" not in item:
            print(f"Invalid override format: {item}", file=sys.stderr)
            return EXIT_CONFIG_ERROR
        key, value_str = item.split("=", 1)
        try:
            value = yaml.safe_load(value_str)
        except yaml.YAMLError:
            value = value_str
        try:
            _apply_override(config, key, value)
        except Exception:
            print(f"Unknown override key: {key}", file=sys.stderr)
            return EXIT_CONFIG_ERROR
    if args.verbose and args.overrides:
        logger.debug("Overrides: %s", args.overrides)

    try:
        nodes = _validate_structure(config)
        inspection = build_pipeline_inspection(nodes)
        validate_pipeline(inspection)
    except Exception as exc:
        print(f"Invalid config: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    ctx_dict: dict[str, Any] = {}
    for item in args.contexts:
        if "=" not in item:
            print(f"Invalid context format: {item}", file=sys.stderr)
            return EXIT_CONFIG_ERROR
        key, value_str = item.split("=", 1)
        try:
            # Parse value using YAML to handle type conversion (1.0 -> float, true -> bool, etc.)
            value = yaml.safe_load(value_str)
        except yaml.YAMLError:
            # Fall back to string if YAML parsing fails
            value = value_str
        ctx_dict[key] = value
    if args.verbose and ctx_dict:
        logger.debug("Injected context: %s", ctx_dict)

    if args.validate:
        if ctx_dict and args.verbose:
            logger.debug("Ignoring --context for validation")
        print("Config valid.")
        return EXIT_SUCCESS

    try:
        trace_driver = None
        if args.trace_driver != "none":
            if args.trace_driver == "jsonl":
                trace_driver = JSONLTrace(args.trace_output, detail=args.trace_detail)
            else:
                if not args.trace_output:
                    print(
                        "--trace-output must specify driver class for pythonpath",
                        file=sys.stderr,
                    )
                    return EXIT_CONFIG_ERROR
                module_path, _, cls_name = args.trace_output.partition(":")
                mod = importlib.import_module(module_path)
                trace_cls = getattr(mod, cls_name)
                trace_driver = trace_cls()
        pipeline = Pipeline(nodes, logger=logger, trace=trace_driver)
        if args.dry_run:
            if ctx_dict and args.verbose:
                logger.debug("Ignoring --context for dry run")
            print(f"Graph: {len(pipeline.nodes)} nodes.")
            print("Dry run OK (no execution performed).")
            return EXIT_SUCCESS
        start = time.time()
        initial_payload = (
            Payload(NoDataType(), ContextType(ctx_dict)) if ctx_dict else None
        )
        pipeline.process(initial_payload)
        duration = time.time() - start
        print(f"✅ Completed in {duration:.2f}s")
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
    _configure_logger(args.verbose, args.quiet)

    config = _load_yaml(Path(args.pipeline))

    if isinstance(config, dict):
        specs = config.get("extensions")
        if not specs and isinstance(config.get("pipeline"), dict):
            specs = config["pipeline"].get("extensions")
        if specs:
            load_extensions(specs)

    try:
        nodes = _validate_structure(config)
        inspection = build_pipeline_inspection(nodes)
        validate_pipeline(inspection)
    except Exception as exc:
        print(f"Invalid config: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    report = (
        extended_report(inspection) if args.extended else summary_report(inspection)
    )
    print(report)
    return EXIT_SUCCESS


def main(argv: List[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.command == "run":
        code = _run(args)
    else:
        code = _inspect(args)
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
