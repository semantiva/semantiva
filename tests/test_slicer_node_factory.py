import pytest
from semantiva.data_types.data_types import DataCollectionType
from semantiva.context_processors.context_types import (
    ContextType,
    ContextCollectionType,
)
from semantiva.context_processors.context_observer import ContextObserver


class MockProcessor:
    """Mock processor class for testing slicer node behavior."""

    @staticmethod
    def get_created_keys():
        return ["processed_key"]

    @staticmethod
    def process(data, context):
        """Mock process method that appends 'processed' to data."""
        context_observer = ContextObserver()
        context_observer.update_context(context, "processed_key", f"processed_{data}")
        return f"processed_{data}", context

    @staticmethod
    def output_type():
        return str
