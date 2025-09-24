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

"""Semantiva Examples Extension.

This lightweight extension exposes example processors for demos and tests.
It provides basic data types and operations commonly used in documentation
and testing scenarios.
"""

from __future__ import annotations

from semantiva.registry import SemantivaExtension
from semantiva.registry.processor_registry import ProcessorRegistry


class SemantivaExamplesExtension(SemantivaExtension):
    """
    Lightweight extension that exposes example processors for demos/tests.

    This extension provides Float-based data types, operations, probes,
    and I/O components that are used throughout the Semantiva documentation
    and test suite.

    Usage in YAML:
        extensions: ["semantiva-examples"]

    Components provided:
    - FloatDataType and FloatDataCollection
    - Float arithmetic operations (add, multiply, divide, etc.)
    - Float data sources and sinks
    - Float probes for inspection and collection
    """

    def register(self) -> None:
        """Register example processors with the ProcessorRegistry."""
        ProcessorRegistry.register_modules(
            [
                "semantiva.examples.test_utils",
            ]
        )
