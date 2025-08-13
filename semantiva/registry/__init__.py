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

from .class_registry import ClassRegistry
from .plugin_registry import SemantivaExtension, load_extensions

# Initialize default modules when the class is loaded
ClassRegistry.initialize_default_modules()

__all__ = [
    "ClassRegistry",
    "SemantivaExtension",
    "load_extensions",
]
