from typing import Type
from semantiva.data_types.data_types import DataCollectionType
from semantiva.data_processors.data_processors import (
    BaseDataProcessor,
    DataOperation,
    DataProbe,
)


class SlicingDataProcessorFactory:
    """
    Factory that dynamically creates data slicer processors.
    """

    @staticmethod
    def create(
        processor_class: Type[BaseDataProcessor],
        input_data_collection_type: Type[DataCollectionType],
    ):
        """
        Creates a new processor class that slices data and manages context.

        Args:
            processor_class (Type): Base processor class.
            input_data_collection_type (Type[DataCollectionType]): Expected input collection type.

        Returns:
            A new processor class with slicing enabled.
        """
        processor_name = processor_class.__name__
        class_name = f"SlicerFor{processor_name}"

        if issubclass(processor_class, DataOperation):

            assert (
                processor_class.input_data_type() == processor_class.output_data_type()
            ), "Data slicing supported only for processors matching input and output data types."

            class SlicingDataOperator(processor_class):  # type: ignore[valid-type, misc]
                """
                Wraps a data operator to handle data slicing.
                """

                data_type_override = input_data_collection_type

                @classmethod
                def input_data_type(cls):
                    return cls.data_type_override

                @classmethod
                def output_data_type(cls):
                    return cls.data_type_override

                def process(
                    self,
                    data,
                    *args,
                    **kwargs,
                ):
                    """
                    Automatically slices input data and manages context.
                    """

                    processed_data = self.data_type_override.from_list([])
                    for idx, data_item in enumerate(data):
                        output = super().process(data_item, *args, **kwargs)
                        processed_data.append(output)

                    return processed_data

            SlicingDataOperator.__name__ = class_name
            return SlicingDataOperator

        elif issubclass(processor_class, DataProbe):

            class SlicingDataProbe(processor_class):  # type: ignore[valid-type, misc]
                """
                Wraps a data probe to handle data slicing.
                """

                input_data_type_override = input_data_collection_type

                @classmethod
                def input_data_type(cls):
                    return cls.input_data_type_override

                def process(
                    self,
                    data,
                    *args,
                    **kwargs,
                ):
                    """
                    Automatically slices input data and manages context.
                    """

                    probed_results = []
                    for idx, data_item in enumerate(data):
                        probed_results.append(
                            super().process(data_item, *args, **kwargs)
                        )

                    return probed_results

            SlicingDataProbe.__name__ = class_name
            return SlicingDataProbe


def Slicer(processor_cls: Type, input_data_collection_type: Type[DataCollectionType]):
    """Convenient user API for creating slicer nodes with explicit types."""
    return SlicingDataProcessorFactory.create(processor_cls, input_data_collection_type)
