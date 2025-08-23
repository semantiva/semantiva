from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any


def _import_from_path(class_path: str):
    module_name, _, cls_name = class_path.rpartition(".")
    module = import_module(module_name)
    return getattr(module, cls_name)


@dataclass
class ModelDescriptor:
    class_path: str
    kwargs: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        return {"class": self.class_path, "kwargs": descriptor_to_json(self.kwargs)}

    def instantiate(self) -> Any:
        cls = _import_from_path(self.class_path)
        kwargs = instantiate_from_descriptor(self.kwargs)
        return cls(**kwargs)


def descriptor_to_json(obj: Any) -> Any:
    if isinstance(obj, ModelDescriptor):
        return obj.to_json()
    if isinstance(obj, dict):
        return {k: descriptor_to_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [descriptor_to_json(v) for v in obj]
    return obj


def instantiate_from_descriptor(obj: Any) -> Any:
    if isinstance(obj, ModelDescriptor):
        return obj.instantiate()
    if isinstance(obj, dict):
        if set(obj.keys()) == {"class", "kwargs"}:
            cls = _import_from_path(obj["class"])
            kwargs = instantiate_from_descriptor(obj.get("kwargs", {}))
            return cls(**kwargs)
        return {k: instantiate_from_descriptor(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [instantiate_from_descriptor(v) for v in obj]
    return obj
