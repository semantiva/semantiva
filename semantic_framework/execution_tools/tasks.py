from abc import ABC, abstractmethod
from typing import Type, Dict, Optional
from ..data_io import PayloadSource, PayloadSink
from ..payload_operations import PayloadOperation


class ComputingTask(ABC):
    """
    Abstract base class for a computing task.

    Subclasses must implement the `_run` method to define the specific computation logic.
    """

    @abstractmethod
    def _run(self, *args, **kwargs):
        """
        Abstract method to be implemented by subclasses for performing the task.

        Args:
            *args: Positional arguments for the task.
            **kwargs: Keyword arguments for the task.
        """
        ...

    def run(self, *args, **kwargs):
        """
        Run the computing task by invoking the `_run` method.

        Args:
            *args: Positional arguments for the task.
            **kwargs: Keyword arguments for the task.

        Returns:
            The result of the `_run` method.
        """
        return self._run(*args, **kwargs)


class PayloadOperationTask(ComputingTask):
    """
    Task for processing payloads using a data source, a payload operation, and a data sink.

    This class encapsulates the logic for:
    - Retrieving data and context from a data source.
    - Applying a payload operation to the data and context.
    - Sending the processed data and context to a data sink.

    Attributes:
        payload_source_class (Type[DataSource]): Class responsible for providing the data.
        payload_source_parameters (Dict): Parameters for initializing the payload source.
        payload_operation_class (Type[PayloadOperation]): Class responsible for the payload operation.
        payload_operation_config (Dict): Configuration for the payload operation.
        payload_sink_class (Type[PayloadSink]): Class responsible for consuming the processed data and context.
        payload_sink_parameters (Dict): Parameters for initializing the payload sink.
    """

    payload_source_class: Type[PayloadSource]
    payload_source_parameters: Dict
    payload_operation_class: Type[PayloadOperation]
    payload_operation_config: Dict
    payload_sink_class: Optional[Type[PayloadSink]]
    payload_sink_parameters: Optional[Dict]

    def __init__(
        self,
        payload_source_class: Type[PayloadSource],
        payload_source_parameters: Dict,
        payload_operation_class: Type[PayloadOperation],
        payload_operation_config: Dict,
        payload_sink_class: Optional[Type[PayloadSink]] = None,
        payload_sink_parameters: Optional[Dict] = None,
    ):
        """
        Initialize the PayloadOperationTask with the required components and configurations.

        Args:
            payload_source_class (Type[DataSource]): The class for the data source.
            payload_source_parameters (Dict): Parameters for initializing the data source.
            payload_operation_class (Type[PayloadOperation]): The class for the payload operation.
            payload_operation_config (Dict): Configuration for the payload operation.
            payload_sink_class (Type[DataSink]): The class for the data sink.
            payload_sink_parameters (Dict): Parameters for initializing the data sink.
        """
        self.payload_source_class = payload_source_class
        self.payload_source_parameters = payload_source_parameters
        self.payload_operation_class = payload_operation_class
        self.payload_operation_config = payload_operation_config
        self.payload_sink_class = payload_sink_class
        self.payload_sink_parameters = payload_sink_parameters

    def _run(self):
        """
        Execute the payload operation task.

        Steps:
        1. Retrieve data and context from the data source.
        2. Apply the payload operation to the data and context.
        3. Send the processed data and context to the data sink.

        Returns:
            tuple: A tuple containing the processed data and context.
        """
        # Retrieve data and context from the data source
        payload_source_instance = self.payload_source_class()
        data, context = payload_source_instance.get_payload(
            **self.payload_source_parameters
        )

        # Initialize and apply the payload operation
        operation = self.payload_operation_class(self.payload_operation_config)

        processed_data, processed_context = operation.process(data, context)

        # Send the processed data and context to the data sink if provided
        if self.payload_sink_class:
            sink_parameters = self.payload_sink_parameters or {}
            payload_sink_instance = self.payload_sink_class()
            payload_sink_instance.send_payload(
                processed_data, processed_context, sink_parameters
            )

        return processed_data, processed_context
