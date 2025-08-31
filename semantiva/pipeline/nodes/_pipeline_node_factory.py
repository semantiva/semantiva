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

from types import new_class
from typing import Any, Dict, Optional, Type, Union
from semantiva.data_processors.io_operation_factory import _IOOperationFactory
from semantiva.data_io import DataSource, PayloadSource, DataSink, PayloadSink
from semantiva.data_processors.data_processors import (
    DataOperation,
    DataProbe,
    _BaseDataProcessor,
)
from semantiva.registry import ClassRegistry
from semantiva.logger import Logger
from semantiva.context_processors import (
    ContextProcessor,
)
from .nodes import (
    _PipelineNode,
    _DataSinkNode,
    _DataSourceNode,
    _PayloadSinkNode,
    _PayloadSourceNode,
    _DataOperationNode,
    _ContextProcessorNode,
    _ContextDataProcessorNode,
    _ProbeContextInjectorNode,
    _ProbeResultCollectorNode,
    _DataOperationContextInjectorProbeNode,
)


def _resolve_class(class_name: Union[str, Type, None]) -> Optional[Type]:
    """Resolve a class name to an actual class using the registry."""
    if isinstance(class_name, str):
        return ClassRegistry.get_class(class_name)
    return class_name


class _PipelineNodeFactory:
    """
    Factory class to create nodes based on the provided configuration.
    """

    @staticmethod
    def _create_class(
        name: str,
        base_cls: Type,
        **class_attrs: Any,
    ) -> Type:
        """
        Dynamically create a subclass of `base_cls` whose namespace is
        pre-populated with `class_attrs`.
        """
        return new_class(
            name,
            (base_cls,),
            {},
            # callback that fills the namespace
            lambda ns: ns.update(class_attrs),
        )

    @staticmethod
    def create_io_node(
        node_definition: Dict,
        logger: Optional[Logger] = None,
    ) -> _PipelineNode:
        """
        Factory function to create an appropriate data I/O node instance based on the given definition.

        Args:
            node_definition (Dict): A dictionary describing the node configuration.
            logger (Optional[Logger]): Optional logger instance for diagnostic messages.

        Returns:
            _PipelineNode: A subclass of _PipelineNode.

        Raises:
            ValueError: If the node definition is invalid or if the processor type is unsupported.
        """
        processor = node_definition.get("processor")
        parameters = node_definition.get("parameters", {})

        # Resolve the processor class if provided as a string.
        processor = _resolve_class(processor)

        if processor is None or not isinstance(processor, type):
            raise ValueError("processor must be a class type or a string, not None.")

        if issubclass(processor, DataSource):
            return _PipelineNodeFactory.create_data_source_node(
                processor, parameters, logger
            )
        if issubclass(processor, PayloadSource):
            return _PipelineNodeFactory.create_payload_source_node(
                processor, parameters, logger
            )
        if issubclass(processor, DataSink):
            return _PipelineNodeFactory.create_data_sink_node(
                processor, parameters, logger
            )
        if issubclass(processor, PayloadSink):
            return _PipelineNodeFactory.create_payload_sink_node(
                processor, parameters, logger
            )

        raise ValueError(
            "Unsupported processor. Processor must be of type DataOperation, DataProbe, DataSource, PayloadSource, DataSink, or PayloadSink."
        )

    @staticmethod
    def create_payload_source_node(
        data_io_class: Type[PayloadSource],
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> _PayloadSourceNode:
        """Factory function to create an extended _PayloadSourceNode.
        This function dynamically creates a subclass of _PayloadSourceNode
        with a specific payload source class and its associated metadata.

        Args:
            data_io_class (Type[PayloadSource]): The class of the payload source to be used.
            parameters (Optional[Dict]): Configuration parameters for the payload source. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        Returns:
            _PayloadSourceNode: An instance of a dynamically created subclass of _PayloadSourceNode.
        """

        # Wrap the data IO class in a DataOperation subclass
        processor = _IOOperationFactory.create_data_operation(data_io_class)

        node_class = _PipelineNodeFactory._create_class(
            name=f"{data_io_class.__name__}_PayloadSourceNode",
            base_cls=_PayloadSourceNode,
            processor=data_io_class,
        )
        return node_class(
            processor=processor, processor_parameters=parameters, logger=logger
        )

    @staticmethod
    def create_payload_sink_node(
        data_io_class: Type[PayloadSink],
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> _PayloadSinkNode:
        """Factory function to create an extended _PayloadSinkNode.
        This function dynamically creates a subclass of _PayloadSinkNode
        with a specific payload sink class and its associated metadata.
        Args:
            data_io_class (Type[PayloadSink]): The class of the payload sink to be used.
            parameters (Optional[Dict]): Configuration parameters for the payload sink. Defaults to None.
        Returns:
            _PayloadSinkNode: An instance of a dynamically created subclass of _PayloadSinkNode.
        """

        processor = _IOOperationFactory.create_data_operation(data_io_class)

        node_class = _PipelineNodeFactory._create_class(
            name=f"{data_io_class.__name__}_PayloadSinkNode",
            base_cls=_PayloadSinkNode,
            processor=data_io_class,
        )
        return node_class(
            processor=processor, processor_parameters=parameters, logger=logger
        )

    @staticmethod
    def create_data_sink_node(
        data_io_class: Type[DataSink],
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> _DataSinkNode:
        """Factory function to create an extended _DataSinkNode.
        This function dynamically creates a subclass of _DataSinkNode
        with a specific data sink class.
        Args:
            data_io_class (Type[DataSink]): The class of the data sink to be used.
            parameters (Optional[Dict]): Configuration parameters for the payload sink. Defaults to None.
        Returns:
            _DataSinkNode: An instance of a dynamically created subclass of _DataSinkNode.
        """

        processor = _IOOperationFactory.create_data_operation(data_io_class)

        node_class = _PipelineNodeFactory._create_class(
            name=f"{data_io_class.__name__}_DataSinkNode",
            base_cls=_DataSinkNode,
            processor=data_io_class,
        )

        return node_class(
            processor=processor, processor_parameters=parameters, logger=logger
        )

    @staticmethod
    def create_data_source_node(
        data_io_class: Type[DataSource],
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> _DataSourceNode:
        """Factory function to create an extended _DataSourceNode.
        This function dynamically creates a subclass of _DataSourceNode
        with a specific data source class.
        Args:
            data_io_class (Type[DataSource]): The class of the data source to be used.
            parameters (Optional[Dict]): Configuration parameters for the data source. Defaults to None.
            logger (Optional[Logger]): A Logger instance. Defaults to None
        Returns:
            _DataSinkNode: An instance of a dynamically created subclass of _DataSourceNode.
        """

        processor = _IOOperationFactory.create_data_operation(data_io_class)

        node_class = _PipelineNodeFactory._create_class(
            name=f"{data_io_class.__name__}_DataSourceNode",
            base_cls=_DataSourceNode,
            processor=data_io_class,
        )

        return node_class(
            processor=processor, processor_parameters=parameters, logger=logger
        )

    @staticmethod
    def create_data_operation_node(
        processor_class: Type[_BaseDataProcessor],
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> _DataOperationNode:
        """Factory function to create an extended _DataOperationNode.
        This function dynamically creates a subclass of _DataOperationNode
        with a specific data source class.
        Args:
            processor_class (Type[_BaseDataProcessor]): The class of the data operation to be used.
            parameters (Optional[Dict]): Configuration parameters for the data source. Defaults to None.
            logger (Optional[Logger]): A Logger instance. Defaults to None
        Returns:
            _DataOperationNode: An instance of a dynamically created subclass of _DataSourceNode.
        """

        node_class = _PipelineNodeFactory._create_class(
            name=f"{processor_class.__name__}_DataOperationNode",
            base_cls=_DataOperationNode,
            processor=processor_class,
        )

        return node_class(
            processor=processor_class, processor_parameters=parameters, logger=logger
        )

    @staticmethod
    def create_probe_context_injector(
        processor_class: Type[_BaseDataProcessor],
        context_keyword: str,
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> _ProbeContextInjectorNode:
        """Factory function to create an extended _ProbeContextInjectorNode.
        This function dynamically creates a subclass of _ProbeContextInjectorNode
        with a specific data processor class.
        Args:
            processor_class (Type[_BaseDataProcessor]): The class of the data operation to be used.
            context_keyword (str): The context key for the probe result.
            parameters (Optional[Dict]): Configuration parameters. Defaults to None.
            logger (Optional[Logger]): A Logger instance. Defaults to None
        Returns:
            _ProbeContextInjectorNode: An instance of a dynamically created subclass of _ProbeContextInjectorNode.
        """

        if not context_keyword or not isinstance(context_keyword, str):
            raise ValueError("context_keyword must be a non-empty string.")

        node_class = _PipelineNodeFactory._create_class(
            name=f"{processor_class.__name__}_ProbeContextInjectorNode",
            base_cls=_ProbeContextInjectorNode,
            processor=processor_class,
            context_keyword=context_keyword,
        )
        return node_class(processor_class, context_keyword, parameters, logger)

    @staticmethod
    def create_data_operation_context_injector_probe_node(
        *,
        processor_cls: Type[DataOperation],
        context_keyword: str,
        **processor_kwargs,
    ) -> _DataOperationContextInjectorProbeNode:
        """Wrap a :class:`DataOperation` in a context-injecting probe node."""

        if (
            not isinstance(processor_cls, type)
            or not issubclass(processor_cls, DataOperation)
            or issubclass(processor_cls, DataProbe)
        ):
            raise ValueError("processor_cls must be a DataOperation subclass")
        if not context_keyword or not isinstance(context_keyword, str):
            raise ValueError("context_keyword must be a non-empty string")

        node_class = _PipelineNodeFactory._create_class(
            name=f"{processor_cls.__name__}_DataOperationContextInjectorProbeNode",
            base_cls=_DataOperationContextInjectorProbeNode,
            processor=processor_cls,
            context_keyword=context_keyword,
        )
        return node_class(processor_cls, context_keyword, processor_kwargs)

    @staticmethod
    def create_probe_result_collector(
        processor_class: Type[_BaseDataProcessor],
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> _ProbeResultCollectorNode:
        """Factory function to create an extended _ProbeResultCollectorNode.
        This function dynamically creates a subclass of _ProbeResultCollectorNode
        with a specific processor class.
        Returns:
            _ProbeResultCollectorNode: An instance of a dynamically created subclass of _ProbeNode.
        """

        node_class = _PipelineNodeFactory._create_class(
            name=f"{processor_class.__name__}_ProbeResultCollectorNode",
            base_cls=_ProbeResultCollectorNode,
            processor=processor_class,
        )
        return node_class(
            processor=processor_class,
            processor_parameters=parameters,
            logger=logger,
        )

    @staticmethod
    def create_context_processor_wrapper_node(
        processor_class: Type[ContextProcessor],
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> _ContextProcessorNode:
        """Factory helper for wrapping :class:`ContextProcessor` classes."""

        parameters = parameters or {}
        context_processor_instance = processor_class(logger)

        node_class = _PipelineNodeFactory._create_class(
            name=f"{processor_class.__name__}_ContextProcessorNode",
            base_cls=_ContextProcessorNode,
            processor=context_processor_instance,
        )
        return node_class(
            processor=processor_class,
            processor_config=parameters,
            logger=logger,
        )

    @staticmethod
    def create_context_processor_node(
        *,
        input_context_keyword: str,
        output_context_keyword: str,
        processor_cls: Type[DataOperation] | Type[DataProbe],
        **processor_kwargs,
    ) -> _ContextDataProcessorNode:
        """Create a node that processes a context value using a data processor."""

        if not (isinstance(input_context_keyword, str) and input_context_keyword):
            raise ValueError("input_context_keyword must be a non-empty string")
        if not (isinstance(output_context_keyword, str) and output_context_keyword):
            raise ValueError("output_context_keyword must be a non-empty string")
        if not (
            isinstance(processor_cls, type)
            and issubclass(processor_cls, (DataOperation, DataProbe))
        ):
            raise ValueError("processor_cls must be a DataProcessor subclass")

        node_class = _PipelineNodeFactory._create_class(
            name=f"{processor_cls.__name__}_ContextDataProcessorNode",
            base_cls=_ContextDataProcessorNode,
            processor_cls=processor_cls,
            input_context_keyword=input_context_keyword,
            output_context_keyword=output_context_keyword,
        )
        return node_class(
            processor_cls,
            input_context_keyword,
            output_context_keyword,
            processor_kwargs,
        )


# Main node factory function
def _pipeline_node_factory(
    node_definition: Dict,
    logger: Optional[Logger] = None,
) -> _PipelineNode:
    """
    Factory function to create an appropriate node instance based on the given definition.

    The node definition dictionary should include:
      - "processor": The class (or a string that can be resolved to a class) for the processor.
      - "parameters": (Optional) A dictionary of parameters for the processor.
      - "context_keyword": (Optional) A string specifying the context key for probe injection.

    Args:
        node_definition (Dict): A dictionary describing the node configuration.
        logger (Optional[Logger]): Optional logger instance for diagnostic messages.

    Returns:
        _PipelineNode: An instance of a subclass of _DataNode or _ContextProcessorNode.

    Raises:
        ValueError: If the node definition is invalid or if the processor type is unsupported.
    """

    # DESIGN NOTE: Structured Parametric Sweep Preprocessing
    # ======================================================
    #
    # The preprocess_node_config step is required due to a fundamental mismatch
    # between the resolver pattern and the structured YAML format for parametric sweeps.
    #
    # WHY RESOLVERS DON'T WORK FOR STRUCTURED FORMAT:
    # 1. Resolvers operate on processor strings (e.g., "sweep:Source:Collection")
    # 2. Structured format requires access to BOTH processor string AND parameters
    # 3. Resolvers only receive the processor string, not the full node configuration
    # 4. The ParametricSweepFactory.create() needs data from the parameters section
    #
    # EXAMPLE OF THE PROBLEM:
    # YAML Input:
    #   processor: "sweep:FloatValueDataSource:FloatDataCollection"  # <- Resolver sees this
    #   parameters:                                                 # <- Resolver cannot see this
    #     num_steps: 5
    #     independent_vars: { t: [0, 10] }
    #
    # PREPROCESSING SOLUTION:
    # - Operates at node configuration level (has access to full context)
    # - Transforms structured sweep configs into resolved processor classes
    # - Maintains backward compatibility with existing resolver architecture
    # - Preserves separation of concerns between different resolver types
    #
    # ALTERNATIVE APPROACHES CONSIDERED:
    # 1. Enhanced Resolver API: Would require breaking changes to all existing resolvers
    # 2. Parameter-aware Resolvers: Complex, violates single responsibility principle
    # 3. Two-phase Resolution: Overly complex for this specific use case
    #
    # The preprocessing approach is the least invasive solution that maintains
    # architectural integrity while enabling the structured YAML format.
    node_definition = ClassRegistry.preprocess_node_config(node_definition)

    processor = node_definition.get("processor")
    parameters = node_definition.get("parameters", {})
    parameters = ClassRegistry.resolve_parameters(parameters)
    node_definition["parameters"] = parameters
    context_keyword = node_definition.get("context_keyword")

    # Resolve the processor class if provided as a string.
    processor = _resolve_class(processor)

    if processor is None or not isinstance(processor, type):
        raise ValueError("processor must be a class type or a string, not None.")

    if issubclass(processor, ContextProcessor):
        # pylint: disable=import-outside-toplevel
        from semantiva.workflows.fitting_model import (
            ModelFittingContextProcessor,
            _model_fitting_processor_factory,
        )

        params = dict(parameters or {})

        # Handle ModelFittingContextProcessor with variable mapping
        if (
            processor is ModelFittingContextProcessor
            and "independent_var_key" in params
            and "dependent_var_key" in params
        ):
            independent_var_key = params.pop("independent_var_key")
            dependent_var_key = params.pop("dependent_var_key")
            context_keyword = params.pop("context_keyword", None)
            processor = _model_fitting_processor_factory(
                independent_var_key=independent_var_key,
                dependent_var_key=dependent_var_key,
                context_keyword=context_keyword,
            )
        elif "context_keyword" in params and hasattr(processor, "with_context_keyword"):
            key = params.pop("context_keyword")
            processor = processor.with_context_keyword(key)

        return _PipelineNodeFactory.create_context_processor_wrapper_node(
            processor, params, logger
        )

    if issubclass(processor, DataOperation):
        if context_keyword is not None:
            raise ValueError(
                "context_keyword must not be defined for DataOperation nodes."
            )
        return _PipelineNodeFactory.create_data_operation_node(
            processor, parameters, logger
        )
    if issubclass(processor, DataProbe):
        if context_keyword is not None:
            return _PipelineNodeFactory.create_probe_context_injector(
                processor, context_keyword, parameters, logger
            )
        else:
            return _PipelineNodeFactory.create_probe_result_collector(
                processor, parameters, logger
            )
    if issubclass(processor, (DataSource, PayloadSource, DataSink, PayloadSink)):
        return _PipelineNodeFactory.create_io_node(node_definition, logger)
    else:
        raise ValueError(
            "Unsupported processor. Processor must be of type DataOperation or DataProbe."
        )
