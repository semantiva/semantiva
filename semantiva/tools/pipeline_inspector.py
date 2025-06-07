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

from typing import List, Any, Dict
import inspect
from semantiva.logger import Logger
from semantiva.exceptions.pipeline import PipelineConfigurationError
from semantiva.payload_operations.pipeline import Pipeline
from semantiva.payload_operations.nodes.nodes import (
    PipelineNode,
    ProbeContextInjectorNode,
    ContextProcessorNode,
)
from semantiva.execution_tools.transport import (
    SemantivaTransport,
)
from semantiva.execution_tools.orchestrator.orchestrator import (
    SemantivaOrchestrator,
)


class PipelineInspector:
    """
    A utility class for inspecting pipeline nodes and configurations.

    Provides methods to analyze the structure, requirements, and behavior of a pipeline,
    producing human-readable summaries and extended reports for debugging and introspection.
    """

    @classmethod
    def _inspect_nodes(cls, nodes: List[PipelineNode]) -> str:
        """
        Inspect a list of PipelineNode objects and return a summary of the pipeline.

        The summary includes:
        - Node details: Class names and operations of the nodes.
        - Parameters: Differentiates between pipeline configuration and context parameters.
        - Context updates: Keywords created, modified, or deleted in the context.
        - Required context keys: Context parameters necessary for the pipeline.
        - Errors for invalid states, such as requiring deleted context keys.

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

        required_context_keys = cls._determine_required_context_keys(
            all_required_params, injected_or_created_keywords
        )

        summary_lines.insert(
            1, f"\tRequired context keys: {cls._format_set(required_context_keys)}"
        )

        return "\n".join(summary_lines)

    @staticmethod
    def _format_set(values: set[str] | list[str]) -> str:
        """
        Format a set or list of strings into a sorted, comma-separated string.

        Args:
            values (set[str] | list[str]): A collection of string values.

        Returns:
            str: Comma-separated sorted values or "None" if empty.
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
        """
        Build a summary for a single node, updating tracking sets.

        Args:
            node (PipelineNode): The pipeline node to summarize.
            index (int): The node's position in the pipeline.
            deleted_keys (set[str]): Keys deleted by previous nodes.
            all_required_params (set[str]): Context keys required by the pipeline.
            injected_or_created_keywords (set[str]): Context keys created or injected by nodes.
            key_origin (dict[str, int]): Mapping of context keys to the node index that created them.

        Returns:
            list[str]: Human-readable lines describing the node.
        """
        operation_params = set(node.processor.get_processing_parameter_names())
        config_params = set(node.processor_config.keys())
        context_params = operation_params - config_params

        all_required_params.update(context_params)

        created_keys = node.processor.get_created_keys()
        injected_or_created_keywords.update(created_keys)

        if isinstance(node, ProbeContextInjectorNode):
            injected_or_created_keywords.add(node.context_keyword)
            created_keys.append(node.context_keyword)
            key_origin[node.context_keyword] = index

        for key in created_keys:
            if key not in key_origin:
                key_origin[key] = index

        cls._validate_deleted_keys(index, operation_params, config_params, deleted_keys)

        node_summary_lines = [
            f"\n\t{index}. Node: {node.processor.__class__.__name__} ({node.get_metadata().get('component_type', 'Unknown')})",
            f"\t\tParameters: {cls._format_set(operation_params)}",
            f"\t\t\tFrom pipeline configuration: {cls._format_pipeline_config(node.processor_config)}",
            f"\t\t\tFrom context: {cls._format_context_params(context_params, key_origin)}",
            f"\t\tContext additions: {cls._format_set(created_keys)}",
        ]

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
        Validate that a node does not require context keys that were previously deleted.

        Args:
            index (int): The node's position in the pipeline.
            operation_params (set[str]): Parameters required by the node.
            config_params (set[str]): Parameters provided by the node's configuration.
            deleted_keys (set[str]): Keys deleted by previous nodes.

        Raises:
            PipelineConfigurationError: If a node requires keys that were deleted and not restored.
        """
        missing_deleted_keys = operation_params & deleted_keys
        if not missing_deleted_keys.issubset(config_params):
            raise PipelineConfigurationError(
                f"Node {index} requires context keys previously deleted: {sorted(missing_deleted_keys)}"
            )

    @staticmethod
    def _determine_required_context_keys(
        all_required_params: set[str],
        injected_or_created_keywords: set[str],
    ) -> set[str]:
        """
        Determine context keys required by the pipeline but not created or injected.

        Args:
            all_required_params (set[str]): Context keys required across the pipeline.
            injected_or_created_keywords (set[str]): Context keys created or injected by nodes.

        Returns:
            set[str]: Context keys required but not provided by any node.
        """
        return all_required_params - injected_or_created_keywords

    @staticmethod
    def _format_pipeline_config(processor_config: dict[str, Any]) -> str:
        """
        Format parameters explicitly set in the pipeline configuration.

        Args:
            processor_config (dict[str, Any]): Processor configuration key-value pairs.

        Returns:
            str: Comma-separated 'key=value' pairs or "None" if empty.
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
        Format context parameters required by a node, including their origin if known.

        Args:
            context_params (set[str]): Context parameters required by the node.
            key_origin (dict[str, int]): Mapping of context keys to the node index that created them.

        Returns:
            str: Comma-separated list of parameters with origins or "None" if empty.
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

    @classmethod
    def inspect_pipeline_extended(cls, pipeline: Pipeline) -> str:
        """
        Perform an extended inspection of a pipeline, providing verbose details.

        Includes per-node details, overall required context keys, and processor docstrings.

        Args:
            pipeline (Pipeline): The pipeline to inspect.

        Returns:
            str: An extended inspection report.
        """
        summary_lines = ["Extended Pipeline Inspection:"]
        footnotes: Dict[str, str] = {}
        all_required: set[str] = set()
        all_created: set[str] = set()

        for index, node in enumerate(pipeline.nodes, start=1):
            metadata = node.get_metadata()
            injected_keys: set[str] = set()
            required_keys: set[str] = set()

            processor = node.processor
            processor_class_name = processor.__class__.__name__

            if hasattr(processor, "get_required_context_keys"):
                required_keys.update(processor.get_required_context_keys())

            if hasattr(processor, "get_required_keys"):
                required_keys.update(processor.get_required_keys())

            suppressed_keys: set[str] = set()
            if hasattr(processor, "get_suppressed_keys"):
                suppressed_keys = set(processor.get_suppressed_keys())

            created_keys: set[str] = set()
            if hasattr(processor, "get_created_keys"):
                created_keys.update(processor.get_created_keys())
                injected_keys |= created_keys

            if isinstance(node, ProbeContextInjectorNode):
                injected_key = getattr(node, "context_keyword", None)
                if injected_key:
                    injected_keys.add(injected_key)
                    created_keys.add(injected_key)

            processor_config = node.processor_config
            config_params_str = (
                ", ".join(f"{k}={v}" for k, v in processor_config.items())
                if processor_config
                else "None"
            )

            all_required.update(required_keys)
            all_created.update(created_keys | injected_keys)

            summary_lines.extend(
                [
                    f"\nNode {index}: {processor_class_name} ({node.__class__.__name__})",
                    f"    - Component type: {metadata.get('component_type')}",
                    f"    - Input data type: {node.input_data_type().__name__ if hasattr(node, 'input_data_type') else 'None'}",
                    f"    - Output data type: {node.output_data_type().__name__ if hasattr(node, 'output_data_type') else 'None'}",
                    f"    - Parameters from pipeline configuration: {config_params_str}",
                    f"    - Parameters from context: {cls._format_set(required_keys)}",
                    f"    - Context additions: {cls._format_set(created_keys | injected_keys)}",
                    f"    - Context suppressions: {cls._format_set(suppressed_keys)}",
                ]
            )

            footnote_key = processor_class_name
            if footnote_key not in footnotes:
                processor_doc = (
                    inspect.getdoc(processor.__class__) or "No description provided."
                )
                footnotes[footnote_key] = processor_doc

        required_final = all_required - all_created
        summary_lines.insert(
            1, f"\tRequired context keys: {cls._format_set(required_final)}"
        )

        summary_lines.append("\nFootnotes:")
        for name, doc in footnotes.items():
            summary_lines.extend([f"[{name}]", doc, ""])

        return "\n".join(summary_lines)

    @classmethod
    def get_nodes_semantic_ids_report(cls, nodes: List[PipelineNode]) -> str:
        """
        Generate a report of semantic IDs for each node in the pipeline.

        Args:
            nodes (List[PipelineNode]): A list of pipeline nodes.

        Returns:
            str: A report containing semantic IDs for each node.
        """
        report = ""

        for index, node in enumerate(nodes, start=1):
            report += f"\nNode {index}:\n"
            report += node.semantic_id()
        return report

    @classmethod
    def inspect_pipeline(cls, pipeline: Pipeline) -> str:
        """
        Inspect an initialized Pipeline instance.

        Args:
            pipeline (Pipeline): The pipeline to inspect.

        Returns:
            str: A summary of the pipeline.
        """
        return cls._inspect_nodes(pipeline.nodes)

    @classmethod
    def inspect_config(
        cls,
        config: List[Dict],
        logger: Logger | None = None,
        transport: SemantivaTransport | None = None,
        orchestrator: SemantivaOrchestrator | None = None,
    ) -> str:
        """
        Initialize a Pipeline from a configuration dictionary list and inspect it.

        Args:
            config (List[Dict]): Pipeline configuration as a list of dictionaries.
            logger (Logger | None): Optional logger instance.
            transport (SemantivaTransport | None): Optional transport instance.
            orchestrator (SemantivaOrchestrator | None): Optional orchestrator instance.

        Returns:
            str: A summary of the pipeline.
        """
        pipeline = Pipeline(
            config, logger=logger, transport=transport, orchestrator=orchestrator
        )
        return cls.inspect_pipeline(pipeline)

    @classmethod
    def inspect_config_extended(
        cls,
        config: List[Dict],
        logger: Logger | None = None,
        transport: SemantivaTransport | None = None,
        orchestrator: SemantivaOrchestrator | None = None,
    ) -> str:
        """
        Initialize a Pipeline from a configuration dictionary list and perform an extended inspection.

        Args:
            config (List[Dict]): Pipeline configuration as a list of dictionaries.
            logger (Logger | None): Optional logger instance.
            transport (SemantivaTransport | None): Optional transport instance.
            orchestrator (SemantivaOrchestrator | None): Optional orchestrator instance.

        Returns:
            str: An extended inspection report of the pipeline.
        """
        pipeline = Pipeline(
            config, logger=logger, transport=transport, orchestrator=orchestrator
        )
        return cls.inspect_pipeline_extended(pipeline)
