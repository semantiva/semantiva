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

"""Public registry interfaces for Semantiva."""

from .bootstrap import RegistryProfile, apply_profile, current_profile
from .builtin_resolvers import register_builtin_resolvers, reset_to_builtins
from .name_resolver_registry import NameResolverRegistry
from .parameter_resolver_registry import (
    ParameterResolverRegistry,
    resolve_parameters,
)
from .plugin_registry import SemantivaExtension, load_extensions
from .processor_registry import ProcessorRegistry
from .resolve import UnknownProcessorError, resolve_symbol

# Ensure built-in resolvers are installed at import time.
register_builtin_resolvers()


__all__ = [
    "ProcessorRegistry",
    "NameResolverRegistry",
    "ParameterResolverRegistry",
    "resolve_parameters",
    "resolve_symbol",
    "UnknownProcessorError",
    "SemantivaExtension",
    "load_extensions",
    "RegistryProfile",
    "apply_profile",
    "current_profile",
    "reset_to_builtins",
]
