class MaxProcessingTimeExceededException(Exception):
    def __init__(self, message="Max processing time limit reached!", details=None):
        super().__init__(message, details)


class FileNotSupportedException(Exception):
    def __init__(self, message="Unsupported file type!", details=None):
        super().__init__(message)
        self.details = details


class Doc2PDFConversionError(Exception):
    def __init__(self, message="Document to PDF conversion error", details=None):
        super().__init__(message)
        self.details = details


class Doc2PDFTimeoutError(Exception):
    def __init__(self, message="Document to PDF Timeout error", details=None):
        super().__init__(message)
        self.details = details


class LLMInteractionError(Exception):
    def __init__(self, message="LLM interaction error", details=None):
        super().__init__(message)
        self.details = details


class PromptInitError(Exception):
    def __init__(self, message="Prompt initialization error", details=None):
        super().__init__(message)
        self.details = details


class FunctionCreationError(Exception):
    def __init__(self, message="OpenAI function creation error", details=None):
        super().__init__(message)
        self.details = details


class FunctionBindingError(Exception):
    def __init__(self, message="Binding error", details=None):
        super().__init__(message)
        self.details = details
