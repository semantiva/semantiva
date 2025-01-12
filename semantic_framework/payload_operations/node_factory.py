from typing import Dict
from ..payload_operations.payload_operations import (
    Node,
    AlgorithmNode,
    ProbeResultColectorNode,
    ProbeContextInjectornode,
)
from ..data_operations.data_operations import DataAlgorithm, DataProbe
from ..context_operations.context_operations import ContextPassthough


def node_factory(node_definition: Dict) -> Node:
    """
    Factory function to create a Node instance based on the given definition.

    Args:
        node_definition (Dict): A dictionary defining the node structure. Expected keys:
            - "operation": An instance of DataOperation (required).
            - "context_operation": An instance of ContextOperation (optional).
            - "parameters": A dictionary of operation parameters (optional).
            - "context_keyword": A string defining a context keyword (optional).

    Returns:
        Node: An instance of the appropriate Node subclass.

    Raises:
        ValueError: If the node definition is invalid or incompatible.
    """
    operation = node_definition.get("operation")
    context_operation = node_definition.get("context_operation", ContextPassthough())
    parameters = node_definition.get("parameters", {})
    context_keyword = node_definition.get("context_keyword")

    if isinstance(operation, DataAlgorithm):
        if context_keyword is not None:
            raise ValueError(
                "context_keyword must not be defined for DataAlgorithm nodes."
            )
        return AlgorithmNode(
            data_operation=operation,
            context_operation=context_operation,
            operation_parameters=parameters,
        )

    elif isinstance(operation, DataProbe):
        if context_keyword is not None:
            return ProbeContextInjectornode(
                data_operation=operation,
                context_operation=context_operation,
                context_keyword=context_keyword,
                operation_parameters=parameters,
            )
        else:
            return ProbeResultColectorNode(
                data_operation=operation,
                context_operation=context_operation,
                operation_parameters=parameters,
            )

    else:
        raise ValueError(
            "Unsupported operation type. Operation must be of type DataAlgorithm or DataProbe."
        )
