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

from typing import Type, List, Any
from semantiva.data_types.data_types import DataCollectionType
from semantiva.data_processors.data_processors import (
    _BaseDataProcessor,
    DataOperation,
    DataProbe,
)


class _SlicingDataProcessorFactory:
    """
    Factory that dynamically creates data slicer processors.
    """

    @staticmethod
    def create(
        processor_class: Type[_BaseDataProcessor],
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
                Data Collection slicer operator.
                """

                data_type_override = input_data_collection_type

                @classmethod
                def input_data_type(cls) -> type[DataCollectionType]:
                    """Return the collection data type consumed by the slicer."""
                    return cls.data_type_override

                @classmethod
                def output_data_type(cls) -> type[DataCollectionType]:
                    """Return the collection data type produced by the slicer."""
                    return cls.data_type_override

                def process(
                    self,
                    data,
                    *args,
                    **kwargs,
                ) -> DataCollectionType:
                    """
                    Automatically slices input data and manages context.
                    """

                    processed_data = self.data_type_override.from_list([])
                    for _, data_item in enumerate(data):
                        output = super().process(data_item, *args, **kwargs)
                        processed_data.append(output)

                    return processed_data

            SlicingDataOperator.__name__ = class_name
            SlicingDataOperator.__doc__ = f"{SlicingDataOperator.__doc__} For each element in the collection: {processor_class.__doc__}"
            return SlicingDataOperator

        elif issubclass(processor_class, DataProbe):

            class SlicingDataProbe(processor_class):  # type: ignore[valid-type, misc]
                """
                Data Collection slicer probe.
                """

                input_data_type_override = input_data_collection_type

                @classmethod
                def input_data_type(cls) -> type[DataCollectionType]:
                    """Return the collection data type consumed by the probe."""
                    return cls.input_data_type_override

                def process(
                    self,
                    data,
                    *args,
                    **kwargs,
                ) -> List[Any]:
                    """
                    Automatically slices input data and manages context.
                    """

                    probed_results = []
                    for data_item in data:
                        probed_results.append(
                            super().process(data_item, *args, **kwargs)
                        )

                    return probed_results

            SlicingDataProbe.__name__ = class_name

            SlicingDataProbe.__doc__ = f"{SlicingDataProbe.__doc__} For each element in the collection: {processor_class.__doc__}"
            return SlicingDataProbe


def slicer(
    processor_cls: Type[_BaseDataProcessor],
    input_data_collection_type: Type[DataCollectionType],
):
    """Convenient user API for creating slicer nodes with explicit types."""
    return _SlicingDataProcessorFactory.create(
        processor_cls, input_data_collection_type
    )
