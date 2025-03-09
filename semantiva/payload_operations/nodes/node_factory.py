from typing import Dict, Optional
from ...logger import Logger
from ...component_loader import ComponentLoader
from ...context_processors.context_processors import ContextProcessor
from ...data_io import DataSource, PayloadSource, DataSink, PayloadSink
from ...data_processors.data_processors import (
    DataOperation,
    DataProbe,
)
from .io_node_factory import DataIONodeFactory
from .nodes import (
    DataNode,
    ContextNode,
    OperationNode,
    ProbeContextInjectorNode,
    ProbeResultCollectorNode,
)


# Main node factory function
def node_factory(
    node_definition: Dict,
    logger: Optional[Logger] = None,
) -> DataNode | ContextNode:
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
        DataNode | ContextNode: An instance of a subclass of DataNode or ContextNode.

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
    elif issubclass(processor, (DataSource, PayloadSource, DataSink, PayloadSink)):
        return DataIONodeFactory.create_io_node(node_definition, logger)
    else:
        raise ValueError(
            "Unsupported processor. Processor must be of type DataOperation or DataProbe."
        )
