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


class MissingRequiredDetailsError(Exception):
    def __init__(self, message="Missing Required Details", details=None):
        super().__init__(message)
        self.details = details


class CommonException(Exception):
    def __init__(self, message="Common exception", details=None):
        super().__init__(message)
        self.details = details


class LanguageModelException(Exception):
    def __init__(self, message="Error while executing language model", details=None):
        super().__init__(message)
        self.details = details
