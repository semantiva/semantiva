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
"""
Semantiva Contract Expectations
===============================

This module is the single source of truth for Semantiva's contract rules:
- RULES: a small, readable catalog (table-driven) with code, severity, title,
  applies_to, trigger/hint, and a 'check' callable per rule.
- validate_component(s): executes RULES and returns Diagnostics (no asserts).
- export_contract_catalog_markdown(): emits the RULES table for docs.

Doctor, tests, and future CI must import and use these functions directly.
Update RULES here once; all tools stay in sync.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple
import inspect
import importlib
import importlib.util
import os
import pkgutil
import pathlib
import sys

from .messages import MESSAGES


# ------------------------------- Diagnostics -------------------------------


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    component: str
    location: Optional[Tuple[str, int]]
    details: Dict[str, Any] = field(default_factory=dict)


def _diag(code: str, severity: str, cls: type, details: Dict[str, Any]) -> Diagnostic:
    msg = MESSAGES[code].format(**details)
    try:
        file = inspect.getsourcefile(cls)
        line = inspect.getsourcelines(cls)[1]
        loc = (file, line) if file else None
    except Exception:  # pragma: no cover - source may be missing
        loc = None
    return Diagnostic(
        code=code,
        severity=severity,
        message=msg,
        component=f"{cls.__module__}.{cls.__qualname__}",
        location=loc,
        details=details,
    )


# -------------------------------- RULE SPECS -------------------------------


@dataclass(frozen=True)
class RuleSpec:
    code: str
    severity: str
    title: str
    applies_to: str
    message_key: str
    hint: str
    trigger: str
    check: Callable[[type, Optional[dict]], List[Diagnostic]]


RULES: List[RuleSpec] = []


# ------------------------------ Rule helpers -------------------------------


def _is_classmethod(cls: type, name: str) -> bool:
    attr = inspect.getattr_static(cls, name, None)
    return isinstance(attr, classmethod)


def _iter_data_type_methods(cls: type) -> List[str]:
    names: List[str] = []
    for n in dir(cls):
        if n.startswith("__") and n.endswith("__"):
            continue
        if n.endswith("_data_type"):
            names.append(n)
    return names


def _list_unique_str(val: Any) -> bool:
    return (
        isinstance(val, list)
        and all(isinstance(x, str) for x in val)
        and len(val) == len(set(val))
    )


# ------------------------------ Rule checks --------------------------------


def _r_input_is_classmethod(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if hasattr(cls, "input_data_type") and not _is_classmethod(cls, "input_data_type"):
        return [_diag("SVA001", "error", cls, {})]
    return []


def _r_output_is_classmethod(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if hasattr(cls, "output_data_type") and not _is_classmethod(
        cls, "output_data_type"
    ):
        return [_diag("SVA002", "error", cls, {})]
    return []


def _r_any_data_type_is_classmethod(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    for name in _iter_data_type_methods(cls):
        if name in ("input_data_type", "output_data_type"):
            continue
        if not _is_classmethod(cls, name):
            diags.append(_diag("SVA003", "error", cls, {}))
    return diags


def _r_data_type_returns_type(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    for name in ("input_data_type", "output_data_type"):
        if not hasattr(cls, name) or not _is_classmethod(cls, name):
            continue
        try:
            rv = getattr(cls, name)()
        except Exception as exc:  # pragma: no cover - defensive
            diags.append(
                _diag("SVA004", "error", cls, {"method": name, "got": repr(exc)})
            )
            continue
        if not isinstance(rv, type):
            diags.append(_diag("SVA004", "error", cls, {"method": name, "got": rv}))
    return diags


def _r_data_source_methods_classmethod(
    cls: type, md: Optional[dict]
) -> List[Diagnostic]:
    """Check that DataSource functional methods are classmethods for stateless operation."""
    if not isinstance(md, dict) or md.get("component_type") != "DataSource":
        return []

    diags: List[Diagnostic] = []

    # Check _get_data method
    if hasattr(cls, "_get_data") and not _is_classmethod(cls, "_get_data"):
        diags.append(_diag("SVA005", "error", cls, {}))

    # Check get_data method
    if hasattr(cls, "get_data") and not _is_classmethod(cls, "get_data"):
        diags.append(_diag("SVA006", "error", cls, {}))

    return diags


def _r_payload_source_methods_classmethod(
    cls: type, md: Optional[dict]
) -> List[Diagnostic]:
    """Check that PayloadSource functional methods are classmethods for stateless operation."""
    if not isinstance(md, dict) or md.get("component_type") != "PayloadSource":
        return []

    diags: List[Diagnostic] = []

    # Check _get_payload method
    if hasattr(cls, "_get_payload") and not _is_classmethod(cls, "_get_payload"):
        diags.append(_diag("SVA007", "error", cls, {}))

    # Check get_payload method
    if hasattr(cls, "get_payload") and not _is_classmethod(cls, "get_payload"):
        diags.append(_diag("SVA008", "error", cls, {}))

    return diags


def _r_data_sink_methods_classmethod(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    """Check that DataSink functional methods are classmethods for stateless operation."""
    if not isinstance(md, dict) or md.get("component_type") != "DataSink":
        return []

    diags: List[Diagnostic] = []

    # Check _send_data method
    if hasattr(cls, "_send_data") and not _is_classmethod(cls, "_send_data"):
        diags.append(_diag("SVA009", "error", cls, {}))

    # Check send_data method
    if hasattr(cls, "send_data") and not _is_classmethod(cls, "send_data"):
        diags.append(_diag("SVA010", "error", cls, {}))

    return diags


def _r_payload_sink_methods_classmethod(
    cls: type, md: Optional[dict]
) -> List[Diagnostic]:
    """Check that PayloadSink functional methods are classmethods for stateless operation."""
    if not isinstance(md, dict) or md.get("component_type") != "PayloadSink":
        return []

    diags: List[Diagnostic] = []

    # Check _send_payload method
    if hasattr(cls, "_send_payload") and not _is_classmethod(cls, "_send_payload"):
        diags.append(_diag("SVA011", "error", cls, {}))

    # Check send_payload method
    if hasattr(cls, "send_payload") and not _is_classmethod(cls, "send_payload"):
        diags.append(_diag("SVA012", "error", cls, {}))

    return diags


def _r_metadata_dict(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    for where in ("_define_metadata", "get_metadata"):
        try:
            rv = getattr(cls, where)()
        except Exception:
            diags.append(_diag("SVA100", "error", cls, {"where": where}))
            continue
        if not isinstance(rv, dict):
            diags.append(_diag("SVA100", "error", cls, {"where": where}))
    return diags


def _r_required_keys(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    required = {"class_name", "docstring", "component_type"}
    missing = sorted(required - md.keys())
    if missing:
        return [_diag("SVA101", "error", cls, {"missing": missing})]
    return []


def _r_docstring_length(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    doc = inspect.getdoc(cls) or ""
    limit = int(os.getenv("SEMANTIVA_DOCSTRING_MAX_CHARS", "600"))
    if len(doc) > limit:
        return [_diag("SVA102", "warn", cls, {"actual": len(doc), "limit": limit})]
    return []


def _r_parameters_shape(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict) or "parameters" not in md:
        return []
    params = md["parameters"]
    if params not in ("None", {}, None) and not isinstance(params, (dict, list)):
        return [_diag("SVA103", "error", cls, {"got": type(params).__name__})]
    return []


def _r_injected_context_keys(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict) or "injected_context_keys" not in md:
        return []
    if not _list_unique_str(md["injected_context_keys"]):
        return [_diag("SVA104", "error", cls, {})]
    return []


def _r_suppressed_context_keys(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict) or "suppressed_context_keys" not in md:
        return []
    if not _list_unique_str(md["suppressed_context_keys"]):
        return [_diag("SVA105", "error", cls, {})]
    return []


def _r_context_keys_overlap(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if (
        not isinstance(md, dict)
        or "injected_context_keys" not in md
        or "suppressed_context_keys" not in md
    ):
        return []
    overlap = sorted(
        set(md["injected_context_keys"]) & set(md["suppressed_context_keys"])
    )
    if overlap:
        return [_diag("SVA106", "warn", cls, {"overlap": overlap})]
    return []


def _r_registry_coherence(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    try:
        from semantiva.core.semantiva_component import get_component_registry

        reg = get_component_registry()
        ctype = md.get("component_type")
        if ctype not in reg or cls not in reg.get(ctype, []):
            return [_diag("SVA107", "error", cls, {"component_type": ctype})]
    except Exception:  # pragma: no cover - registry failures ignored
        return []
    return []


def _r_source_requires_output(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    if (
        md.get("component_type") in {"DataSource", "PayloadSource"}
        and "output_data_type" not in md
    ):
        return [_diag("SVA200", "error", cls, {})]
    return []


def _r_source_forbid_input(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    if (
        md.get("component_type") in {"DataSource", "PayloadSource"}
        and "input_data_type" in md
    ):
        return [_diag("SVA201", "warn", cls, {})]
    return []


def _r_sink_requires_input(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    if (
        md.get("component_type") in {"DataSink", "PayloadSink"}
        and "input_data_type" not in md
    ):
        return [_diag("SVA210", "error", cls, {})]
    return []


def _r_sink_forbid_output(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    if (
        md.get("component_type") in {"DataSink", "PayloadSink"}
        and "output_data_type" in md
    ):
        return [_diag("SVA211", "warn", cls, {})]
    return []


def _r_operation_require_both(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    if md.get("component_type") == "DataOperation" and (
        "input_data_type" not in md or "output_data_type" not in md
    ):
        return [_diag("SVA220", "error", cls, {})]
    return []


def _r_operation_parameters(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict) or md.get("component_type") != "DataOperation":
        return []
    return _r_parameters_shape(cls, md)


def _r_probe_require_input(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    if md.get("component_type") == "DataProbe" and "input_data_type" not in md:
        return [_diag("SVA230", "error", cls, {})]
    return []


def _r_probe_no_output(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    if md.get("component_type") == "DataProbe" and "output_data_type" in md:
        return [_diag("SVA231", "warn", cls, {})]
    return []


def _r_probe_parameters(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict) or md.get("component_type") != "DataProbe":
        return []
    return _r_parameters_shape(cls, md)


def _r_context_processor_info(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    if md.get("component_type") == "ContextProcessor":
        return []  # Informational only
    return []


def _r_context_processor_no_operate_context_override(
    cls: type, md: Optional[dict]
) -> List[Diagnostic]:
    """Check that ContextProcessor doesn't override operate_context method."""
    if not isinstance(md, dict) or md.get("component_type") != "ContextProcessor":
        return []

    # Check if the class defines operate_context in its own __dict__ (not inherited)
    if hasattr(cls, "operate_context") and "operate_context" in cls.__dict__:
        return [_diag("SVA241", "error", cls, {})]
    return []


def _r_source_node_input_no_data(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    ctype = md.get("component_type")
    if (
        ctype in {"DataSourceNode", "PayloadSourceNode"}
        and md.get("input_data_type") != "NoDataType"
    ):
        return [_diag("SVA300", "error", cls, {})]
    return []


def _r_source_node_output_matches(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    ctype = md.get("component_type")
    if ctype not in {"DataSourceNode", "PayloadSourceNode"}:
        return []
    proc = getattr(cls, "processor", None)
    if (
        proc is None
        or not hasattr(proc, "output_data_type")
        or not _is_classmethod(proc, "output_data_type")
    ):
        return []
    try:
        expected = proc.output_data_type().__name__
    except Exception:  # pragma: no cover
        return []
    if md.get("output_data_type") != expected:
        return [
            _diag(
                "SVA301",
                "error",
                cls,
                {"node": md.get("output_data_type"), "proc": expected},
            )
        ]
    return []


def _r_sink_node_pass_through(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    ctype = md.get("component_type")
    if ctype not in {"DataSinkNode", "PayloadSinkNode"}:
        return []
    if md.get("input_data_type") != md.get("output_data_type"):
        return [_diag("SVA310", "error", cls, {})]
    return []


def _r_sink_node_matches_processor(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    ctype = md.get("component_type")
    if ctype not in {"DataSinkNode", "PayloadSinkNode"}:
        return []
    proc = getattr(cls, "processor", None)
    if (
        proc is None
        or not hasattr(proc, "input_data_type")
        or not _is_classmethod(proc, "input_data_type")
    ):
        return []
    try:
        expected = proc.input_data_type().__name__
    except Exception:  # pragma: no cover
        return []
    if md.get("input_data_type") != expected or md.get("output_data_type") != expected:
        return [
            _diag(
                "SVA311",
                "error",
                cls,
                {
                    "node_in": md.get("input_data_type"),
                    "node_out": md.get("output_data_type"),
                    "proc": expected,
                },
            )
        ]
    return []


def _r_probe_node_pass_through(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    if md.get("component_type") not in {
        "ProbeContextInjectorNode",
        "ProbeResultCollectorNode",
    }:
        return []
    if md.get("input_data_type") != md.get("output_data_type"):
        return [_diag("SVA320", "error", cls, {})]
    return []


def _r_probe_node_matches_processor(cls: type, md: Optional[dict]) -> List[Diagnostic]:
    if not isinstance(md, dict):
        return []
    if md.get("component_type") not in {
        "ProbeContextInjectorNode",
        "ProbeResultCollectorNode",
    }:
        return []
    proc = getattr(cls, "processor", None)
    if (
        proc is None
        or not hasattr(proc, "input_data_type")
        or not _is_classmethod(proc, "input_data_type")
    ):
        return []
    try:
        expected = proc.input_data_type().__name__
    except Exception:  # pragma: no cover
        return []
    if md.get("input_data_type") != expected or md.get("output_data_type") != expected:
        return [
            _diag(
                "SVA321",
                "error",
                cls,
                {
                    "node_in": md.get("input_data_type"),
                    "node_out": md.get("output_data_type"),
                    "proc": expected,
                },
            )
        ]
    return []


# --------------------------- Validation entrypoints -------------------------


def validate_component(cls: type) -> List[Diagnostic]:
    md = None
    try:
        val = getattr(cls, "get_metadata")()
        if isinstance(val, dict):
            md = val
    except Exception:  # pragma: no cover - metadata getter may fail
        md = None

    diags: List[Diagnostic] = []
    for spec in RULES:
        diags.extend(spec.check(cls, md))
    return diags


def validate_components(
    classes: Iterable[type], debug_mode: bool = False
) -> List[Diagnostic]:
    import logging

    logger = logging.getLogger("Semantiva")
    out: List[Diagnostic] = []

    for c in classes:
        component_name = f"{c.__module__}.{c.__qualname__}"

        if debug_mode:
            # Determine component type based on base classes and attributes
            component_type = "Unknown"
            try:
                # Get the class hierarchy to determine component type
                class_hierarchy = [cls.__name__ for cls in c.__mro__]
                module_name = c.__module__

                if "Pipeline" in class_hierarchy:
                    component_type = "Pipeline"
                elif any(
                    name in class_hierarchy
                    for name in ["ContextProcessor", "ModelFittingContextProcessor"]
                ):
                    component_type = "ContextProcessor"
                elif "DataOperation" in class_hierarchy or "Operation" in c.__name__:
                    component_type = "DataOperation"
                elif "DataProbe" in class_hierarchy or "Probe" in c.__name__:
                    component_type = "DataProbe"
                elif (
                    any(
                        name in class_hierarchy
                        for name in ["DataSource", "PayloadSource"]
                    )
                    or "Source" in c.__name__
                ):
                    component_type = "DataSource"
                elif (
                    any(name in class_hierarchy for name in ["DataSink", "PayloadSink"])
                    or "Sink" in c.__name__
                ):
                    component_type = "DataSink"
                elif "DataType" in class_hierarchy or any(
                    x in c.__name__
                    for x in ["DataType", "Collection", "Image", "Stack"]
                ):
                    component_type = "DataType"
                elif "_SemantivaComponent" in class_hierarchy:
                    component_type = "SemantivaComponent"
                elif "data_io" in module_name:
                    component_type = "DataIO"
                elif "processing" in module_name or "operations" in module_name:
                    component_type = "DataOperation"
                elif "probes" in module_name:
                    component_type = "DataProbe"

            except Exception:
                pass

            logger.debug(f"Validating {component_type}: {component_name}")

            # List applicable rules
            applicable_rules = []
            for rule in RULES:
                # Check if rule applies to this component
                applies_to_lower = rule.applies_to.lower()
                if (
                    applies_to_lower in ["any", "all"]
                    or component_type.lower() in applies_to_lower
                    or "class" in applies_to_lower
                ):
                    applicable_rules.append(rule)

            if applicable_rules:
                rule_codes = [rule.code for rule in applicable_rules]
                logger.debug(f"  Checking rules: {', '.join(rule_codes)}")
            else:
                logger.debug("  No specific rules apply")

        component_diags = validate_component(c)
        out.extend(component_diags)

        if debug_mode and component_diags:
            for diag in component_diags:
                logger.debug(f"  {diag.severity.upper()} {diag.code}: {diag.message}")
        elif debug_mode:
            logger.debug("  ✓ All checks passed")

    return out


# ------------------------------ Discovery helpers --------------------------


def discover_from_registry() -> List[type]:
    from semantiva.core.semantiva_component import get_component_registry
    from semantiva.data_processors.data_processors import DataOperation, DataProbe
    from semantiva.data_io.data_io import DataSource, PayloadSource

    reg = get_component_registry()
    classes = {
        cls
        for bucket in reg.values()
        for cls in bucket
        if not (cls.__name__.startswith("_") and cls.__name__ != "_SemantivaComponent")
        and cls not in {DataOperation, DataProbe, DataSource, PayloadSource}
    }
    return sorted(classes, key=lambda c: f"{c.__module__}.{c.__qualname__}")


def discover_from_modules(mods: Iterable[str]) -> List[type]:
    import logging

    logger = logging.getLogger("Semantiva")
    successfully_imported = []

    for m in mods:
        try:
            module = importlib.import_module(m)
            successfully_imported.append(m)

            # Look for SemantivaExtension subclasses and auto-register them
            try:
                from semantiva.registry import SemantivaExtension

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, SemantivaExtension)
                        and attr != SemantivaExtension
                    ):
                        # Create instance and register
                        extension_instance = attr()
                        extension_instance.register()
                        logger.info(f"Auto-registered extension: {attr.__name__}")

                        # For known extensions, force import their component modules
                        if attr.__name__ == "ImagingExtension":
                            imaging_modules = [
                                "semantiva_imaging.processing.operations",
                                "semantiva_imaging.probes.probes",
                                "semantiva_imaging.data_io.loaders_savers",
                                "semantiva_imaging.adapters.opencv_library.builders",
                            ]
                            for img_mod in imaging_modules:
                                try:
                                    importlib.import_module(img_mod)
                                except Exception as e:
                                    logger.debug(
                                        f"Failed to import imaging module '{img_mod}': {e}"
                                    )

            except Exception as e:
                logger.debug(
                    f"Extension auto-registration failed for module '{m}': {e}"
                )

        except Exception as e:
            logger.warning(f"Failed to import module '{m}': {e}")
            continue

    from semantiva.registry.class_registry import ClassRegistry

    ClassRegistry.register_modules(successfully_imported)
    return discover_from_registry()


def discover_from_paths(paths: Iterable[str]) -> List[type]:
    from semantiva.registry.class_registry import ClassRegistry
    import logging

    logger = logging.getLogger("Semantiva")
    ClassRegistry.register_paths(list(paths))

    for p in paths:
        pp = pathlib.Path(p)
        if pp.is_file() and pp.suffix == ".py":
            try:
                spec = importlib.util.spec_from_file_location(pp.stem, pp)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[pp.stem] = mod
                    spec.loader.exec_module(mod)
            except Exception as e:
                logger.warning(f"Failed to import module from file {pp}: {e}")
                continue
        elif pp.is_dir():
            for mi in pkgutil.walk_packages([str(pp)]):
                try:
                    __import__(mi.name)
                except Exception as e:
                    logger.warning(f"Failed to import module '{mi.name}': {e}")
                    continue
    return discover_from_registry()


def discover_from_extensions(specs: Iterable[str]) -> List[type]:
    from semantiva.registry.plugin_registry import load_extensions

    load_extensions(list(specs))
    return discover_from_registry()


def discover_from_pipeline_yaml(yaml_paths: Iterable[str]) -> List[type]:
    from semantiva.configurations.load_pipeline_from_yaml import (
        load_pipeline_from_yaml,
    )
    from semantiva.registry.class_registry import ClassRegistry

    for yp in yaml_paths:
        # Load the pipeline configuration
        nodes = load_pipeline_from_yaml(yp)

        # Resolve all processor names to ensure they're imported and registered
        for node in nodes:
            processor_spec = node.get("processor")
            if isinstance(processor_spec, str):
                try:
                    # This will import the module and register the component via metaclass
                    ClassRegistry.get_class(processor_spec)
                except Exception:
                    # Ignore resolution errors during discovery
                    pass

    return discover_from_registry()


def discover_from_classes(classes: Iterable[type]) -> List[type]:
    return list(classes)


# ------------------------------- Exporter ----------------------------------


def export_contract_catalog_markdown(path: Optional[str] = None) -> str:
    lines = []
    lines.append("| Code | Severity | Applies To | Summary | Trigger | Hint |")
    lines.append("|------|----------|------------|---------|---------|------|")
    for r in RULES:
        lines.append(
            f"| {r.code} | {r.severity} | {r.applies_to} | {r.title} | {r.trigger} | {r.hint} |"
        )
    md = "\n".join(lines)
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(md + "\n")
    return md


# -------------------------- RULE REGISTRATION ------------------------------


RULES += [
    RuleSpec(
        "SVA001",
        "error",
        "input_data_type must be @classmethod",
        "Any class defining input_data_type",
        "SVA001",
        "Add @classmethod and use cls",
        "Method exists; inspect.getattr_static not classmethod",
        _r_input_is_classmethod,
    ),
    RuleSpec(
        "SVA002",
        "error",
        "output_data_type must be @classmethod",
        "Any class defining output_data_type",
        "SVA002",
        "Add @classmethod and use cls",
        "Method exists; inspect.getattr_static not classmethod",
        _r_output_is_classmethod,
    ),
    RuleSpec(
        "SVA003",
        "error",
        "*_data_type must be @classmethod",
        "Any class defining *_data_type",
        "SVA003",
        "Add @classmethod and use cls",
        "Name matches .*_data_type$",
        _r_any_data_type_is_classmethod,
    ),
    RuleSpec(
        "SVA004",
        "error",
        "*_data_type returns a type",
        "Any class defining *_data_type",
        "SVA004",
        "Return a type (e.g., MyType)",
        "Return is non-type or call raises",
        _r_data_type_returns_type,
    ),
    RuleSpec(
        "SVA005",
        "error",
        "DataSource methods must be @classmethod for stateless operation",
        "DataSource",
        "SVA005",
        "Add @classmethod decorator and use cls parameter",
        "_get_data or get_data not classmethod",
        _r_data_source_methods_classmethod,
    ),
    RuleSpec(
        "SVA007",
        "error",
        "PayloadSource methods must be @classmethod for stateless operation",
        "PayloadSource",
        "SVA007",
        "Add @classmethod decorator and use cls parameter",
        "_get_payload or get_payload not classmethod",
        _r_payload_source_methods_classmethod,
    ),
    RuleSpec(
        "SVA009",
        "error",
        "DataSink methods must be @classmethod for stateless operation",
        "DataSink",
        "SVA009",
        "Add @classmethod decorator and use cls parameter",
        "_send_data or send_data not classmethod",
        _r_data_sink_methods_classmethod,
    ),
    RuleSpec(
        "SVA011",
        "error",
        "PayloadSink methods must be @classmethod for stateless operation",
        "PayloadSink",
        "SVA011",
        "Add @classmethod decorator and use cls parameter",
        "_send_payload or send_payload not classmethod",
        _r_payload_sink_methods_classmethod,
    ),
    RuleSpec(
        "SVA100",
        "error",
        "_define_metadata/get_metadata return dict",
        "All components",
        "SVA100",
        "Return dict",
        "Returned value not dict or raised",
        _r_metadata_dict,
    ),
    RuleSpec(
        "SVA101",
        "error",
        "Required metadata keys present",
        "All components",
        "SVA101",
        "Add missing keys",
        "Missing any of class_name, docstring, component_type",
        _r_required_keys,
    ),
    RuleSpec(
        "SVA102",
        "warn",
        "Docstring too long",
        "All components",
        "SVA102",
        "Shorten summary",
        "len(docstring) > LIMIT",
        _r_docstring_length,
    ),
    RuleSpec(
        "SVA103",
        "error",
        "parameters shape",
        "All components (if parameters present)",
        "SVA103",
        "Normalize params",
        "Not in {dict, list, 'None', {}}",
        _r_parameters_shape,
    ),
    RuleSpec(
        "SVA104",
        "error",
        "injected_context_keys list[str] unique",
        "All components (if present)",
        "SVA104",
        "Fix list",
        "Not list of unique strings",
        _r_injected_context_keys,
    ),
    RuleSpec(
        "SVA105",
        "error",
        "suppressed_context_keys list[str] unique",
        "All components (if present)",
        "SVA105",
        "Fix list",
        "Not list of unique strings",
        _r_suppressed_context_keys,
    ),
    RuleSpec(
        "SVA106",
        "warn",
        "Injected vs suppressed overlap",
        "All components (if both present)",
        "SVA106",
        "Reconcile keys",
        "set(injected) ∩ set(suppressed) non-empty",
        _r_context_keys_overlap,
    ),
    RuleSpec(
        "SVA107",
        "error",
        "Registry/category coherence",
        "All components",
        "SVA107",
        "Fix registration",
        "Not present under its component_type in registry",
        _r_registry_coherence,
    ),
    RuleSpec(
        "SVA200",
        "error",
        "Require output_data_type",
        "DataSource / PayloadSource (component)",
        "SVA200",
        "Add method/meta",
        "Metadata lacks output_data_type",
        _r_source_requires_output,
    ),
    RuleSpec(
        "SVA201",
        "warn",
        "Forbid input_data_type",
        "DataSource / PayloadSource (component)",
        "SVA201",
        "Remove it",
        "Metadata has input_data_type",
        _r_source_forbid_input,
    ),
    RuleSpec(
        "SVA210",
        "error",
        "Require input_data_type",
        "DataSink / PayloadSink (component)",
        "SVA210",
        "Add method/meta",
        "Metadata lacks input_data_type",
        _r_sink_requires_input,
    ),
    RuleSpec(
        "SVA211",
        "warn",
        "Forbid output_data_type",
        "DataSink / PayloadSink (component)",
        "SVA211",
        "Remove it",
        "Metadata has output_data_type",
        _r_sink_forbid_output,
    ),
    RuleSpec(
        "SVA220",
        "error",
        "Require both input & output",
        "DataOperation (component)",
        "SVA220",
        "Add both",
        "One or both missing",
        _r_operation_require_both,
    ),
    RuleSpec(
        "SVA221",
        "error",
        "Parameters shape valid",
        "DataOperation (component)",
        "SVA221",
        "Fix params",
        "Same validator as SVA103",
        _r_operation_parameters,
    ),
    RuleSpec(
        "SVA230",
        "error",
        "Require input_data_type",
        "DataProbe (component)",
        "SVA230",
        "Add method/meta",
        "Missing input",
        _r_probe_require_input,
    ),
    RuleSpec(
        "SVA231",
        "warn",
        "Discourage output_data_type",
        "DataProbe (component)",
        "SVA231",
        "Remove it (node enforces pass-through)",
        "Has output",
        _r_probe_no_output,
    ),
    RuleSpec(
        "SVA232",
        "error",
        "Parameters shape valid",
        "DataProbe (component)",
        "SVA232",
        "Fix params",
        "Same validator as SVA103",
        _r_probe_parameters,
    ),
    RuleSpec(
        "SVA240",
        "info",
        "No IO req; classmethod rules still apply if present",
        "ContextProcessor (component)",
        "SVA240",
        "—",
        "—",
        _r_context_processor_info,
    ),
    RuleSpec(
        "SVA241",
        "error",
        "ContextProcessor must not override operate_context",
        "ContextProcessor (component)",
        "SVA241",
        "Remove operate_context override and implement only _process_logic",
        "Class defines operate_context method in __dict__",
        _r_context_processor_no_operate_context_override,
    ),
    RuleSpec(
        "SVA300",
        "error",
        "Node input is NoDataType",
        "DataSourceNode / PayloadSourceNode (node)",
        "SVA300",
        "Set to NoDataType",
        "Node metadata input != NoDataType",
        _r_source_node_input_no_data,
    ),
    RuleSpec(
        "SVA301",
        "error",
        "Node out == processor out",
        "DataSourceNode / PayloadSourceNode (node)",
        "SVA301",
        "Mirror processor",
        "If processor available, mismatch",
        _r_source_node_output_matches,
    ),
    RuleSpec(
        "SVA310",
        "error",
        "Node input==output (pass-through)",
        "DataSinkNode / PayloadSinkNode (node)",
        "SVA310",
        "Make equal",
        "Mismatch",
        _r_sink_node_pass_through,
    ),
    RuleSpec(
        "SVA311",
        "error",
        "Node I/O == processor input",
        "DataSinkNode / PayloadSinkNode (node)",
        "SVA311",
        "Mirror processor",
        "If processor available, mismatch",
        _r_sink_node_matches_processor,
    ),
    RuleSpec(
        "SVA320",
        "error",
        "Node input==output (pass-through)",
        "Probe Nodes (node)",
        "SVA320",
        "Make equal",
        "Mismatch",
        _r_probe_node_pass_through,
    ),
    RuleSpec(
        "SVA321",
        "error",
        "Node I/O == processor input",
        "Probe Nodes (node)",
        "SVA321",
        "Mirror processor",
        "If processor available, mismatch",
        _r_probe_node_matches_processor,
    ),
]
