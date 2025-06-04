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
from typing import Any, Dict, Optional, Type
from semantiva.data_processors.data_io_wrapper_factory import DataIOWrapperFactory
from semantiva.data_io import DataSource, PayloadSource, DataSink, PayloadSink
from semantiva.data_processors import DataOperation, DataProbe, BaseDataProcessor
from semantiva.component_loader import ComponentLoader
from semantiva.logger import Logger
from semantiva.context_processors import (
    ContextProcessor,
)
from .nodes import (
    PipelineNode,
    PayloadSourceNode,
    PayloadSinkNode,
    DataSinkNode,
    DataSourceNode,
    DataOperationNode,
    ProbeContextInjectorNode,
    ProbeResultCollectorNode,
    ContextProcessorNode,
)


class NodeFactory:
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
        pre‑populated with `class_attrs`.
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
    ) -> PipelineNode:
        """
        Factory function to create an appropriate data I/O node instance based on the given definition.

        Args:
            node_definition (Dict): A dictionary describing the node configuration.
            logger (Optional[Logger]): Optional logger instance for diagnostic messages.

        Returns:
            PipelineNode: A subclass of PipelineNode.

        Raises:
            ValueError: If the node definition is invalid or if the processor type is unsupported.
        """
        processor = node_definition.get("processor")
        parameters = node_definition.get("parameters", {})

        def get_class(class_name):
            """Helper function to retrieve the class from the loader if the input is a string."""
            if isinstance(class_name, str):
                return ComponentLoader.get_class(class_name)
            return class_name

        # Resolve the processor class if provided as a string.
        processor = get_class(processor)

        if processor is None or not isinstance(processor, type):
            raise ValueError("processor must be a class type or a string, not None.")

        if issubclass(processor, DataSource):
            return NodeFactory.create_data_source_node(processor, parameters, logger)
        if issubclass(processor, PayloadSource):
            return NodeFactory.create_payload_source_node(processor, parameters, logger)
        if issubclass(processor, DataSink):
            return NodeFactory.create_data_sink_node(processor, parameters)
        if issubclass(processor, PayloadSink):
            return NodeFactory.create_payload_sink_node(processor, parameters)

        raise ValueError(
            "Unsupported processor. Processor must be of type DataOperation, DataProbe, DataSource, PayloadSource, DataSink, or PayloadSink."
        )

    @staticmethod
    def create_payload_source_node(
        data_io_class: Type[PayloadSource],
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> PayloadSourceNode:
        """Factory function to create an extended PayloadSourceNode.
        This function dynamically creates a subclass of PayloadSourceNode
        with a specific payload source class and its associated metadata.

        Args:
            data_io_class (Type[PayloadSource]): The class of the payload source to be used.
            parameters (Optional[Dict]): Configuration parameters for the payload source. Defaults to None.
            logger (Optional[Logger]): A logger instance for logging messages. Defaults to None.
        Returns:
            PayloadSourceNode: An instance of a dynamically created subclass of PayloadSourceNode.
        """

        # Wrap the data IO class in a DataOperation subclass
        processor = DataIOWrapperFactory.create_data_operation(data_io_class)

        node_class = NodeFactory._create_class(
            name="PayloadSourceNode",
            base_cls=PayloadSourceNode,
            processor=data_io_class,
        )
        return node_class(
            processor=processor, processor_parameters=parameters, logger=logger
        )

    @staticmethod
    def create_payload_sink_node(
        data_io_class: Type[PayloadSink], parameters: Optional[Dict] = None
    ) -> PayloadSinkNode:
        """Factory function to create an extended PayloadSinkNode.
        This function dynamically creates a subclass of PayloadSinkNode
        with a specific payload sink class and its associated metadata.
        Args:
            data_io_class (Type[PayloadSink]): The class of the payload sink to be used.
            parameters (Optional[Dict]): Configuration parameters for the payload sink. Defaults to None.
        Returns:
            PayloadSinkNode: An instance of a dynamically created subclass of PayloadSinkNode.
        """

        processor = DataIOWrapperFactory.create_data_operation(data_io_class)

        node_class = NodeFactory._create_class(
            name=f"{data_io_class.__name__}PayloadSinkNode",
            base_cls=PayloadSinkNode,
            processor=data_io_class,
        )
        return node_class(processor=processor, processor_parameters=parameters)

    @staticmethod
    def create_data_sink_node(
        data_io_class: Type[DataSink], parameters: Optional[Dict] = None
    ) -> DataSinkNode:
        """Factory function to create an extended DataSinkNode.
        This function dynamically creates a subclass of DataSinkNode
        with a specific data sink class.
        Args:
            data_io_class (Type[DataSink]): The class of the data sink to be used.
            parameters (Optional[Dict]): Configuration parameters for the payload sink. Defaults to None.
        Returns:
            DataSinkNode: An instance of a dynamically created subclass of DataSinkNode.
        """

        processor = DataIOWrapperFactory.create_data_operation(data_io_class)

        node_class = NodeFactory._create_class(
            name=f"{data_io_class.__name__}DataSinkNode",
            base_cls=DataSinkNode,
            processor=data_io_class,
        )

        return node_class(processor=processor, processor_parameters=parameters)

    @staticmethod
    def create_data_source_node(
        data_io_class: Type[DataSource],
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> DataSourceNode:
        """Factory function to create an extended DataSourceNode.
        This function dynamically creates a subclass of DataSourceNode
        with a specific data source class.
        Args:
            data_io_class (Type[DataSource]): The class of the data source to be used.
            parameters (Optional[Dict]): Configuration parameters for the data source. Defaults to None.
            logger (Optional[Logger]): A Logger instance. Defaults to None
        Returns:
            DataSinkNode: An instance of a dynamically created subclass of DataSourceNode.
        """

        processor = DataIOWrapperFactory.create_data_operation(data_io_class)

        node_class = NodeFactory._create_class(
            name="DataSourceNode",
            base_cls=DataSourceNode,
            processor=data_io_class,
        )

        return node_class(
            processor=processor, processor_parameters=parameters, logger=logger
        )

    @staticmethod
    def create_data_operation_node(
        processor_class: Type[BaseDataProcessor],
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> DataOperationNode:
        """Factory function to create an extended DataOperationNode.
        This function dynamically creates a subclass of DataOperationNode
        with a specific data source class.
        Args:
            processor_class (Type[BaseDataProcessor]): The class of the data operation to be used.
            parameters (Optional[Dict]): Configuration parameters for the data source. Defaults to None.
            logger (Optional[Logger]): A Logger instance. Defaults to None
        Returns:
            DataOperationNode: An instance of a dynamically created subclass of DataSourceNode.
        """

        node_class = NodeFactory._create_class(
            name=f"{processor_class.__name__}DataOperationNode",
            base_cls=DataOperationNode,
            processor=processor_class,
        )

        return node_class(
            processor=processor_class, processor_parameters=parameters, logger=logger
        )

    @staticmethod
    def create_probe_context_injector(
        processor_class: Type[BaseDataProcessor],
        context_keyword: str,
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> ProbeContextInjectorNode:
        """Factory function to create an extended ProbeContextInjectorNode.
        This function dynamically creates a subclass of ProbeContextInjectorNode
        with a specific data processor class.
        Args:
            processor_class (Type[BaseDataProcessor]): The class of the data operation to be used.
            context_keyword (str): The context key for the probe result.
            parameters (Optional[Dict]): Configuration parameters. Defaults to None.
            logger (Optional[Logger]): A Logger instance. Defaults to None
        Returns:
            ProbeContextInjectorNode: An instance of a dynamically created subclass of ProbeContextInjectorNode.
        """

        if not context_keyword or not isinstance(context_keyword, str):
            raise ValueError("context_keyword must be a non-empty string.")

        node_class = NodeFactory._create_class(
            name=f"{processor_class.__name__}ProbeContextInjectorNode",
            base_cls=ProbeContextInjectorNode,
            processor=processor_class,
            context_keyword=context_keyword,
        )
        return node_class(processor_class, context_keyword, parameters, logger)

    @staticmethod
    def create_probe_result_collector(
        processor_class: Type[BaseDataProcessor],
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> ProbeResultCollectorNode:
        """Factory function to create an extended ProbeResultCollectorNode.
        This function dynamically creates a subclass of ProbeResultCollectorNode
        with a specific processor class.
        Returns:
            ProbeResultCollectorNode: An instance of a dynamically created subclass of ProbeNode.
        """

        node_class = NodeFactory._create_class(
            name=f"{processor_class.__name__}ProbeResultCollectorNode",
            base_cls=ProbeResultCollectorNode,
            processor=processor_class,
        )
        return node_class(
            processor=processor_class,
            processor_parameters=parameters,
            logger=logger,
        )

    @staticmethod
    def create_context_processor_node(
        processor_class: Type[ContextProcessor],
        parameters: Optional[Dict] = None,
        logger: Optional[Logger] = None,
    ) -> ContextProcessorNode:
        """Factory function to create an extended ContextProcessorNode.
        This function dynamically creates a subclass of ContextProcessorNode
        with a specific data processor class.
        Args:
            processor_class (Type[ContextProcessor]): The class of the context processor to be used.
            parameters (Optional[Dict]): Configuration parameters for the context processor. Defaults to None.
            logger (Optional[Logger]): A Logger instance. Defaults to None
        Returns:
            ContextProcessorNode: An instance of a dynamically created subclass of ContextProcessorNode.
        """

        # Ensure parameters is a dictionary
        parameters = parameters or {}
        context_processor_instance = processor_class(logger, **parameters)

        node_class = NodeFactory._create_class(
            name=f"{processor_class.__name__}ContextProcessorNode",
            base_cls=ContextProcessorNode,
            processor=context_processor_instance,
        )
        return node_class(
            processor=processor_class,
            processor_config=parameters,
            logger=logger,
        )


# Main node factory function
def node_factory(
    node_definition: Dict,
    logger: Optional[Logger] = None,
) -> PipelineNode:
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
        PipelineNode: An instance of a subclass of DataNode or ContextProcessorNode.

    Raises:
        ValueError: If the node definition is invalid or if the processor type is unsupported.
    """

    def get_class(class_name):
        """Helper function to retrieve the class from the loader if the input is a string."""
        if isinstance(class_name, str):
            return ComponentLoader.get_class(class_name)
        return class_name

    processor = node_definition.get("processor")
    parameters = node_definition.get("parameters", {})
    context_keyword = node_definition.get("context_keyword")

    # Resolve the processor class if provided as a string.
    processor = get_class(processor)

    if processor is None or not isinstance(processor, type):
        raise ValueError("processor must be a class type or a string, not None.")

    if issubclass(processor, ContextProcessor):
        return NodeFactory.create_context_processor_node(processor, parameters, logger)

    if issubclass(processor, DataOperation):
        if context_keyword is not None:
            raise ValueError(
                "context_keyword must not be defined for DataOperation nodes."
            )
        return NodeFactory.create_data_operation_node(processor, parameters, logger)
    if issubclass(processor, DataProbe):
        if context_keyword is not None:
            return NodeFactory.create_probe_context_injector(
                processor, context_keyword, parameters, logger
            )
        else:
            return NodeFactory.create_probe_result_collector(
                processor, parameters, logger
            )
    if issubclass(processor, (DataSource, PayloadSource, DataSink, PayloadSink)):
        return NodeFactory.create_io_node(node_definition, logger)
    else:
        raise ValueError(
            "Unsupported processor. Processor must be of type DataOperation or DataProbe."
        )
