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
"""Centralized diagnostic message templates for Semantiva contracts."""

MESSAGES = {
    # Classmethod & callable
    "SVA001": "Method `input_data_type` must be a @classmethod (callable as cls.input_data_type()).",
    "SVA002": "Method `output_data_type` must be a @classmethod (callable as cls.output_data_type()).",
    "SVA003": "Methods ending with `_data_type` must be @classmethods.",
    "SVA004": "`{method}` must return a type (got {got!r}).",
    "SVA005": "Method `_get_data` must be a @classmethod for stateless data sources.",
    "SVA006": "Method `get_data` must be a @classmethod for stateless data sources.",
    "SVA007": "Method `_get_payload` must be a @classmethod for stateless payload sources.",
    "SVA008": "Method `get_payload` must be a @classmethod for stateless payload sources.",
    "SVA009": "Method `_send_data` must be a @classmethod for stateless data sinks.",
    "SVA010": "Method `send_data` must be a @classmethod for stateless data sinks.",
    "SVA011": "Method `_send_payload` must be a @classmethod for stateless payload sinks.",
    "SVA012": "Method `send_payload` must be a @classmethod for stateless payload sinks.",
    # Global
    "SVA100": "`{where}` must return dict.",
    "SVA101": "Metadata must include keys: class_name, docstring, component_type.",
    "SVA102": "Docstring exceeds recommended length ({actual} > {limit}). Consider a concise summary.",
    "SVA103": "`parameters` must be dict, list, 'None', or {}.",
    "SVA104": "`injected_context_keys` must be a list of unique strings.",
    "SVA105": "`suppressed_context_keys` must be a list of unique strings.",
    "SVA106": "`injected_context_keys` overlaps `suppressed_context_keys`: {overlap}.",
    "SVA107": "Component registry/category mismatch for {component_type}.",
    # Category (components)
    "SVA200": "DataSource/PayloadSource must define `output_data_type` in metadata.",
    "SVA201": "DataSource/PayloadSource should not define `input_data_type` in metadata.",
    "SVA210": "DataSink/PayloadSink must define `input_data_type` in metadata.",
    "SVA211": "DataSink/PayloadSink should not define `output_data_type` in metadata.",
    "SVA220": "DataOperation must define `input_data_type` and `output_data_type` in metadata.",
    "SVA221": "Parameters shape invalid for DataOperation.",
    "SVA230": "DataProbe must define `input_data_type` in metadata.",
    "SVA231": "DataProbe should omit `output_data_type` in metadata (pass-through semantics).",
    "SVA232": "Parameters shape invalid for DataProbe.",
    "SVA240": "ContextProcessor has no IO requirements; classmethod rules still apply if present.",
    "SVA241": "ContextProcessor must not override operate_context method. Implement _process_logic instead.",
    # Node wrappers
    "SVA300": "Source Node input type must be NoDataType.",
    "SVA301": "Source Node output must equal processor.output_data_type().__name__ (got {node} vs {proc}).",
    "SVA310": "Sink Node input/output must match (pass-through).",
    "SVA311": "Sink Node input/output must both equal processor.input_data_type().__name__ (got {node_in}/{node_out} vs {proc}).",
    "SVA320": "Probe Node input/output must match (pass-through).",
    "SVA321": "Probe Node input/output must both equal processor.input_data_type().__name__ (got {node_in}/{node_out} vs {proc}).",
}
