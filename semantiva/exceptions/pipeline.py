# Description: Custom exceptions for the semantiva package.


class PipelineConfigurationError(Exception):
    """Raised when the pipeline configuration is invalid."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class PipelineTopologyError(Exception):
    """Raised when the pipeline topology is invalid."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message
