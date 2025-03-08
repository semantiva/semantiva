from ...data_io.data_io import DataSource, PayloadSource, DataSink, PayloadSink
from typing import List, Any, Dict, Optional, Type, Tuple
from .nodes import (
    DataNode,
    ContextNode,
    OperationNode,
    ProbeContextInjectorNode,
    ProbeResultCollectorNode,
)
from ...context_processors.context_processors import ContextProcessor
from ...logger import Logger
from ...data_processors.data_processors import (
    DataOperation,
    DataProbe,
)
from .io_nodes import DataSourceNode, PayloadSourceNode, DataSinkNode, PayloadSinkNode
from ...component_loader import ComponentLoader


class DataIONodeFactory:
    """
    Factory class to create data I/O nodes based on the provided configuration.

    This class extends the existing node_factory to support the creation of data I/O nodes.
    """

    @staticmethod
    def create_io_node(
        node_definition: Dict,
        logger: Optional[Logger] = None,
    ) -> DataNode | ContextNode:
        """
        Factory function to create an appropriate data I/O node instance based on the given definition.

        Args:
            node_definition (Dict): A dictionary describing the node configuration.
            logger (Optional[Logger]): Optional logger instance for diagnostic messages.

        Returns:
            DataNode | ContextNode: An instance of a subclass of DataNode or ContextNode.

        Raises:
            ValueError: If the node definition is invalid or if the processor type is unsupported.
        """
        processor = node_definition.get("processor")
        parameters = node_definition.get("parameters", {})
        context_keyword = node_definition.get("context_keyword")

        def get_class(class_name):
            """Helper function to retrieve the class from the loader if the input is a string."""
            if isinstance(class_name, str):
                return ComponentLoader.get_class(class_name)
            return class_name

        # Resolve the processor class if provided as a string.
        processor = get_class(processor)

        if processor is None or not isinstance(processor, type):
            raise ValueError("processor must be a class type or a string, not None.")

        if issubclass(processor, ContextProcessor):
            return ContextNode(processor, processor_config=parameters, logger=logger)

        elif issubclass(processor, DataOperation):
            if context_keyword is not None:
                raise ValueError(
                    "context_keyword must not be defined for DataOperation nodes."
                )
            return OperationNode(
                processor=processor,
                processor_parameters=parameters,
                logger=logger,
            )
        elif issubclass(processor, DataProbe):
            if context_keyword is not None:
                return ProbeContextInjectorNode(
                    processor=processor,
                    context_keyword=context_keyword,
                    processor_parameters=parameters,
                    logger=logger,
                )
            else:
                return ProbeResultCollectorNode(
                    processor=processor,
                    processor_parameters=parameters,
                    logger=logger,
                )
        elif issubclass(processor, DataSource):
            return DataSourceNode(
                data_io_class=processor,
                processor_parameters=parameters,
                logger=logger,
            )
        elif issubclass(processor, PayloadSource):
            return PayloadSourceNode(
                data_io_class=processor,
                processor_parameters=parameters,
                logger=logger,
            )
        elif issubclass(processor, DataSink):
            return DataSinkNode(
                data_io_class=processor,
                processor_parameters=parameters,
            )
        elif issubclass(processor, PayloadSink):
            return PayloadSinkNode(
                data_io_class=processor,
                processor_parameters=parameters,
            )
        else:
            raise ValueError(
                "Unsupported processor. Processor must be of type DataOperation, DataProbe, DataSource, PayloadSource, DataSink, or PayloadSink."
            )
