import inspect
from typing import Type, List
from ..data_types.data_types import BaseDataType, NoDataType
from ..context_processors.context_types import ContextType
from ..data_io import DataSource, PayloadSource, DataSink, PayloadSink
from ..data_processors.data_processors import (
    DataOperation,
)


class DataIOWrapperFactory:
    """
    A factory class for wrapping data IO classes into data processors.

    This class provides a method for creating a data processor instance based on the provided class name.
    """

    @classmethod
    def create_data_operation(
        cls,
        data_io_class: (
            Type[DataSource] | Type[PayloadSource] | Type[DataSink] | Type[PayloadSink]
        ),
    ):
        """
        Dynamically creates a subclass of DataOperation that wraps a data IO class.

        Args:
            data_io_class (Type[DataSource] | Type[PayloadSource] | Type[DataSink] | Type[PayloadSink]):
                The data IO class to wrap in a DataOperation subclass.
        Returns:
            Type[DataOperation]: A new subclass of DataOperation with the specified I/O data types.
        """

        methods: dict = {}

        if issubclass(data_io_class, (DataSource, PayloadSource)):

            def input_data_type_method() -> Type[BaseDataType]:
                return NoDataType

            def output_data_type_method() -> Type[BaseDataType]:
                return type(data_io_class.output_data_type())

            if issubclass(data_io_class, DataSource):

                def _process_logic_method(
                    self, data: BaseDataType, *args, **kwargs
                ) -> BaseDataType:
                    data_io_instance = data_io_class()
                    loaded_data = data_io_instance.get_data(*args, **kwargs)
                    return loaded_data

                def get_processing_parameter_names(cls) -> List[str]:
                    """
                    Retrieve the names of parameters required by the `_get_data` method.

                    Returns:
                        List[str]: A list of parameter names (excluding `self` and `data`).
                    """
                    my_class = data_io_class()
                    print(data_io_class.__dict__)
                    signature = inspect.signature(data_io_class._get_data)
                    return [
                        param.name
                        for param in signature.parameters.values()
                        if param.name not in {"self", "data"}
                        and param.kind
                        not in {
                            inspect.Parameter.VAR_POSITIONAL,
                            inspect.Parameter.VAR_KEYWORD,
                        }
                    ]

        elif issubclass(data_io_class, (DataSink, PayloadSink)):

            def input_data_type_method() -> Type[BaseDataType]:
                return type(data_io_class.input_data_type())

            def output_data_type_method() -> Type[BaseDataType]:
                return type(data_io_class.input_data_type())

        else:
            raise ValueError(f"Invalid data IO class: {data_io_class}.")

        methods["_process_logic"] = _process_logic_method
        methods["input_data_type"] = staticmethod(input_data_type_method)
        methods["output_data_type"] = staticmethod(output_data_type_method)
        methods["get_processing_parameter_names"] = classmethod(
            get_processing_parameter_names
        )

        # Create a new type that extends DataOperation
        class_name = f"{data_io_class.__name__}"
        generated_class = type(class_name, (DataOperation,), methods)
        return generated_class
