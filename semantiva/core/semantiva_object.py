import inspect
import textwrap
from typing import Dict, Any, Callable, List, Tuple
from abc import ABC, abstractmethod


class SemantivaObject(ABC):
    """
    The foundational base class for Semantiva components, providing a unified metadata interface.

    Public Methods:
    - get_metadata() -> Dict[str, Any]: Returns structured metadata about the component.
    - semantic_id() -> str: Returns a human- and LLM-friendly string representation
                            of the same metadata, for quick inspection.

    Abstract Method:
    - _define_metadata() -> Dict[str, Any]: Must be implemented by subclasses to define
                                           component-specific metadata.
    """

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """
        Gathers metadata in dictionary form, combining:
        - Default or framework-level fields
        - Component-specific fields via _define_metadata()
        """
        # Base metadata, applicable to all SemantivaObjects
        docstring_content = inspect.getdoc(cls)
        if docstring_content is None:
            docstring_content = "No documentation available."
        base_metadata = {
            "class_name": cls.__name__,
            "docstring": (docstring_content.strip()),
        }

        # Merge in subclass-defined metadata
        component_metadata = cls._define_metadata()
        if not isinstance(component_metadata, dict):
            raise TypeError(
                "Metadata returned by _define_metadata() must be a dictionary."
            )

        # Merge dictionaries, letting subclass fields overwrite or extend base fields
        combined_metadata = {**base_metadata, **component_metadata}
        return combined_metadata

    @classmethod
    def semantic_id(cls) -> str:
        """
        Presents the metadata in a structured, readable format.
        Useful for quick debugging, LLM-based queries, or
        human inspection in logs/dashboards.
        """
        metadata = cls.get_metadata()

        # We'll temporarily pop the docstring so we can process it separately
        docstring = metadata.pop("docstring", None)
        processor_docstring = metadata.pop("processor_docstring", None)

        # We'll create lines in a list, then join them
        lines = []
        lines.append("========  SEMANTIC ID  ========")
        lines.append(f"Class Name: {metadata.get('class_name', 'Unknown')}")
        metadata.pop("class_name", None)  # Remove the class name from the metadata
        lines.append("===============================")
        # Handle docstring separately if present
        if docstring and docstring.strip():
            lines.append(" - Docstring:")
            # Wrap and indent docstring for clarity
            for doc_line in docstring.strip().splitlines():
                # textwrap can further wrap lines if they're too long:
                wrapped_lines = textwrap.wrap(doc_line, width=100)
                for wline in wrapped_lines:
                    lines.append(f"    {wline}")

        # Now handle all other metadata fields
        # (If you have nested dicts, you might want a recursive approach)
        for key, value in metadata.items():
            if isinstance(value, dict):
                lines.append(f" - {key}:")
                for subkey, subval in value.items():
                    lines.append(f"  {subkey}: {subval}")
            elif isinstance(value, list):
                lines.append(f" - {key}:")
                for item in value:
                    lines.append(f"      - {item}")
            else:

                lines.append(f" - {key}: {value}")

        # Handle wrapped processor docstring separately if present
        if processor_docstring and processor_docstring.strip():
            lines.append(" - Processor docstring:")
            # Wrap and indent for clarity
            for doc_line in processor_docstring.strip().splitlines():
                wrapped_lines = textwrap.wrap(doc_line, width=100)
                for wline in wrapped_lines:
                    lines.append(f"    {wline}")
        lines.append("===============================")
        return "\n".join(lines)

    @classmethod
    @abstractmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        """
        Subclasses implement this method to provide
        component-specific metadata fields.

        For example:
        - role: The role of this component in a pipeline (e.g., 'DataSource', 'Processor')
        - configuration: Param-value pairs relevant to this component
        - dynamic state: Additional fields that might appear
                         only when the object is instantiated
                         in a certain context
        """

    @staticmethod
    def _retrieve_parameter_signatures(
        class_attribute: Callable, excluded_parameters: List[str]
    ) -> List[Tuple[str, str]]:
        """
        Retrieve the names and type hints of parameters required by a method.
        """

        signature = inspect.signature(class_attribute)
        param_type_list = [
            (
                param.name,
                (
                    param.annotation.__name__
                    if param.annotation != param.empty
                    else "Unknown"
                ),
            )
            for param in signature.parameters.values()
            if param.name not in excluded_parameters
            and param.kind
            not in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
        ]

        return param_type_list
