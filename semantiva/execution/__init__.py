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

"""Semantiva execution engine.

This package provides the core execution infrastructure for running Semantiva pipelines.
It includes orchestrators for managing pipeline execution, transports for inter-node
communication, and integration with the tracing system for comprehensive error handling
and execution monitoring.

Key Components:
- LocalSemantivaOrchestrator: Sequential pipeline execution with error tracing
- Transport implementations: In-memory and other data passing strategies
- Error handling: Comprehensive exception capture and trace resource management
"""
