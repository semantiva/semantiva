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

from typing import List, Any
from semantiva.exceptions.pipeline import PipelineConfigurationError
from .nodes.nodes import PipelineNode, ProbeContextInjectorNode, ContextProcessorNode


class PipelineInspector:
    """
    A utility class that inspects a sequence of pipeline nodes, producing a
    human-readable summary of the pipeline's structure and requirements.
    """

    @classmethod
    def inspect(cls, nodes: List[PipelineNode]) -> str:
        """
        Inspect a list of PipelineNode objects and return a comprehensive summary.

        The summary covers:
            • Node details: The class names of the nodes and their operations.
            • Parameters: Which parameters come from the pipeline configuration versus the context.
            • Context updates: The keywords that each node creates, modifies, or deletes in the context.
            • Required context keys: The set of context parameters necessary for the pipeline.
            • Errors for invalid states, such as requiring context keys that have been deleted.

        Args:
            nodes (List[PipelineNode]): A list of pipeline nodes in execution order.

        Returns:
            str: A formatted report describing the pipeline composition and relevant details.
        """
        summary_lines = ["Pipeline Structure:"]
        all_required_params: set[str] = set()
        injected_or_created_keywords: set[str] = set()
        deleted_keys: set[str] = set()
        key_origin: dict[str, int] = {}

        for index, node in enumerate(nodes, start=1):
            node_summary = cls._build_node_summary(
                node=node,
                index=index,
                deleted_keys=deleted_keys,
                all_required_params=all_required_params,
                injected_or_created_keywords=injected_or_created_keywords,
                key_origin=key_origin,
            )
            summary_lines.extend(node_summary)

        # Calculate context keys required by the pipeline but not created/injected anywhere
        required_context_keys = cls._determine_required_context_keys(
            all_required_params, injected_or_created_keywords
        )

        # Insert the required context keys right after the main title
        summary_lines.insert(
            1, f"\tRequired context keys: {cls._format_set(required_context_keys)}"
        )

        return "\n".join(summary_lines)

    @staticmethod
    def _format_set(values: set[str] | list[str]) -> str:
        """
        Convert a set/list of strings into a sorted, comma-separated string.
        Returns "None" if the set/list is empty.

        Args:
            values (set[str] | list[str]): A collection of string values.

        Returns:
            str: Comma-separated sorted values or "None".
        """
        return ", ".join(sorted(values)) if values else "None"

    @classmethod
    def _build_node_summary(
        cls,
        node: PipelineNode,
        index: int,
        deleted_keys: set[str],
        all_required_params: set[str],
        injected_or_created_keywords: set[str],
        key_origin: dict[str, int],
    ) -> list[str]:
        """Build a summary for a single node, updating tracking sets."""
        # Identify operation/config parameters
        operation_params = set(node.processor.get_processing_parameter_names())
        config_params = set(node.processor_config.keys())
        context_params = operation_params - config_params

        # Track needed context keys
        all_required_params.update(context_params)

        # Track newly created keys
        created_keys = node.processor.get_created_keys()
        injected_or_created_keywords.update(created_keys)

        # If the node is a ProbeContextInjectorNode, add the context keyword to the set
        if isinstance(node, ProbeContextInjectorNode):
            injected_or_created_keywords.add(node.context_keyword)
            created_keys.append(node.context_keyword)
            key_origin[node.context_keyword] = index

        # Record origins of any keys created by this node
        for key in created_keys:
            if key not in key_origin:
                key_origin[key] = index

        # Validate the node doesn't require keys that were previously deleted
        cls._validate_deleted_keys(index, operation_params, config_params, deleted_keys)

        # Build human-readable lines describing this node
        node_summary_lines = [
            f"\n\t{index}. Node: {node.processor.__class__.__name__} ({node.get_metadata().get('component_type', 'Unknown')})",
            f"\t\tParameters: {cls._format_set(operation_params)}",
            f"\t\t\tFrom pipeline configuration: {cls._format_pipeline_config(node.processor_config)}",
            f"\t\t\tFrom context: {cls._format_context_params(context_params, key_origin)}",
            f"\t\tContext additions: {cls._format_set(created_keys)}",
        ]

        # Add context suppressions if the node is a ContextProcessorNode
        if isinstance(node, ContextProcessorNode):
            suppressed_keys = node.get_suppressed_keys()
            deleted_keys.update(suppressed_keys)
            node_summary_lines.append(
                f"\t\tContext suppressions: {cls._format_set(suppressed_keys)}"
            )

        return node_summary_lines

    @staticmethod
    def _validate_deleted_keys(
        index: int,
        operation_params: set[str],
        config_params: set[str],
        deleted_keys: set[str],
    ) -> None:
        """
        Ensure that this node does not require context keys that were previously deleted.
        If it does, verify they are re-injected by configuration before raising an error.

        Args:
            index (int): The node's position in the pipeline.
            operation_params (set[str]): The operation parameters this node requires.
            config_params (set[str]): The node's configuration parameters.
            deleted_keys (set[str]): Keys that have been deleted in previous nodes.

        Raises:
            PipelineConfigurationError: If a node requires keys that have been deleted and not restored by config.
        """
        missing_deleted_keys = operation_params & deleted_keys
        if not missing_deleted_keys.issubset(config_params):
            raise PipelineConfigurationError(
                f"Node {index} requires context keys previously deleted: {missing_deleted_keys}"
            )

    @staticmethod
    def _determine_required_context_keys(
        all_required_params: set[str],
        injected_or_created_keywords: set[str],
    ) -> set[str]:
        """
        Determine which context keys the pipeline ultimately needs but doesn't create or inject.

        Args:
            all_required_params (set[str]): All context parameters required across the pipeline.
            injected_or_created_keywords (set[str]): All context keys that are created or injected.

        Returns:
            set[str]: The subset of required context parameters not provided by any node.
        """
        return all_required_params - injected_or_created_keywords

    @staticmethod
    def _format_pipeline_config(processor_config: dict[str, Any]) -> str:
        """
        Produce a string describing parameters explicitly set in the pipeline configuration.

        Args:
            processor_config (dict[str, Any]): Processor configuration key-value pairs.

        Returns:
            str: A comma-separated list of 'key=value' pairs, or 'None' if empty.
        """
        if processor_config:
            return ", ".join(
                f"{key}={value}" for key, value in processor_config.items()
            )
        return "None"

    @staticmethod
    def _format_context_params(
        context_params: set[str], key_origin: dict[str, int]
    ) -> str:
        """
        Produce a string describing which context params a node requires, optionally including
        the node of origin if the parameter was created earlier in the pipeline.

        Args:
            context_params (set[str]): Context parameters the node requires.
            key_origin (dict[str, int]): A map of param -> node index that created it.

        Returns:
            str: A comma-separated list of parameters, including their origin if known, or 'None' if empty.
        """
        if not context_params:
            return "None"
        parts = []
        for param in sorted(context_params):
            if param in key_origin:
                origin_node = key_origin[param]
                parts.append(f"{param} (from Node {origin_node})")
            else:
                parts.append(param)
        return ", ".join(parts)
