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

"""Pipeline Introspection Module.

This module provides a comprehensive pipeline introspection system that separates
concerns into three distinct layers:

1. **Builder Layer** (:mod:`semantiva.inspection.builder`):
   - Constructs structured inspection data from pipelines or configurations
   - Never raises exceptions - captures errors as inspection data instead
   - Provides unified data structures for all downstream consumers

2. **Reporter Layer** (:mod:`semantiva.inspection.reporter`):
   - Formats inspection data for different consumption needs
   - Supports textual summaries, extended reports, and JSON representations
   - Ensures consistent presentation across CLI tools and web interfaces

3. **Validator Layer** (:mod:`semantiva.inspection.validator`):
   - Validates inspection data and raises structured exceptions when needed
   - Operates on inspection results rather than during pipeline construction
   - Enables inspection of partially valid or invalid configurations

Key Features:
- **Error Resilient**: Inspects invalid configurations without aborting
- **Parameter Tracking**: Tracks parameter resolution from config vs. context
- **Context Flow Analysis**: Traces context key creation, usage, and deletion
- **Multi-format Output**: Supports human-readable and machine-readable formats
- **Origin Traceability**: Records which nodes create or consume context keys
"""

from .builder import NodeInspection, PipelineInspection, build_pipeline_inspection
from .reporter import (
    summary_report,
    extended_report,
    json_report,
    parameter_resolutions,
)
from .validator import validate_pipeline

__all__ = [
    "NodeInspection",
    "PipelineInspection",
    "build_pipeline_inspection",
    "summary_report",
    "extended_report",
    "json_report",
    "parameter_resolutions",
    "validate_pipeline",
]
