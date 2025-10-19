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

"""Semantiva tracing (SER v1).

This package provides the core tracing infrastructure for Semantiva pipelines
based on the Semantic Execution Record (SER). Each completed node emits a single
``SERRecord`` capturing the processor/node, dependencies, context_delta, assertions,
timing (wall and CPU) information, optional tags/summaries, and status.
Drivers implement the :class:`~semantiva.trace.model.TraceDriver` protocol to
persist these records.
"""
