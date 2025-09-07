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
"""Contracts module providing rule validations for Semantiva components."""

from .expectations import (
    Diagnostic,
    validate_component,
    validate_components,
    discover_from_registry,
    discover_from_modules,
    discover_from_paths,
    discover_from_extensions,
    discover_from_pipeline_yaml,
    discover_from_classes,
    export_contract_catalog_markdown,
)
from . import messages

__all__ = [
    "Diagnostic",
    "validate_component",
    "validate_components",
    "discover_from_registry",
    "discover_from_modules",
    "discover_from_paths",
    "discover_from_extensions",
    "discover_from_pipeline_yaml",
    "discover_from_classes",
    "export_contract_catalog_markdown",
    "messages",
]
