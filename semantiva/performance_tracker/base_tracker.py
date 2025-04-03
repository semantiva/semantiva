from abc import ABC, abstractmethod


class BaseTracker(ABC):
    """Abstract class for tracking performance metrics."""

    enabled: bool

    def __init__(self) -> None:
        """Initialize the tracker."""
        self.enabled = True

    def enable(self) -> None:
        """Enable tracking."""
        self.enabled = True

    def disable(self) -> None:
        """Disable tracking."""
        self.enabled = False

    @abstractmethod
    def start(self) -> None:
        """Start tracking."""

    @abstractmethod
    def stop(self) -> None:
        """Stop tracking."""

    @abstractmethod
    def reset(self) -> None:
        """Reset tracking metrics."""

    @abstractmethod
    def __str__(self):
        """Return a string representation of the tracker."""
