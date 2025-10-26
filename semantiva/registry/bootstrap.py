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

"""Registry bootstrap profiles for Semantiva."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Dict, List

from .plugin_registry import load_extensions
from .processor_registry import ProcessorRegistry


DEFAULT_MODULES = [
    "semantiva.context_processors.context_processors",
    "semantiva.data_processors.data_dump",
    "semantiva.data_processors.copy_data_probe",
    "semantiva.workflows.fitting_model",
]


@dataclass(frozen=True)
class RegistryProfile:
    """Serializable description of the registry state required by a job."""

    load_defaults: bool = True
    modules: List[str] = field(default_factory=list)
    paths: List[str] = field(default_factory=list)
    extensions: List[str] = field(default_factory=list)

    def fingerprint(self) -> str:
        """Return a stable SHA-256 fingerprint of the profile."""

        payload = {
            "load_defaults": bool(self.load_defaults),
            "modules": sorted(set(self.modules)),
            "paths": sorted(set(self.paths)),
            "extensions": sorted(set(self.extensions)),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def as_dict(self) -> Dict[str, object]:
        """Return a plain dictionary representation suitable for transport."""

        return {
            "load_defaults": bool(self.load_defaults),
            "modules": list(self.modules),
            "paths": list(self.paths),
            "extensions": list(self.extensions),
        }


def apply_profile(profile: RegistryProfile) -> None:
    """Apply the provided registry profile in the current process."""

    if profile.load_defaults:
        ProcessorRegistry.register_modules(DEFAULT_MODULES)
    if profile.modules:
        ProcessorRegistry.register_modules(profile.modules)
    if profile.extensions:
        load_extensions(profile.extensions)


def current_profile() -> RegistryProfile:
    """Capture the current registry state as a profile."""

    modules = sorted(ProcessorRegistry.module_history())
    paths: List[str] = []
    return RegistryProfile(
        load_defaults=True, modules=modules, paths=paths, extensions=[]
    )
