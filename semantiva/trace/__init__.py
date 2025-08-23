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

"""Semantiva tracing (v1).

This package provides the core tracing infrastructure for Semantiva pipelines.
It implements a contract-based system for capturing execution events with
configurable detail levels and pluggable storage backends.

The tracing system captures complete execution records including error events
with timing data, exception details, and proper resource cleanup for failed pipelines.

Core Components:
- NodeTraceEvent: Standard envelope for all node execution events (before/after/error)
- TraceDriver: Protocol for implementing custom storage backends
- JSONLTrace: Default append-only JSONL driver with background buffering and error handling
"""
