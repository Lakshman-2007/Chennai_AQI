"""
Custom Exceptions and Exception Handlers for Chennai Air Quality Framework.
Conforms to PRD v2.2 C-01 & C-10: Controlled machine-readable error responses.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

class ModelNotReadyException(Exception):
    """
    Raised when prediction or explanation endpoints are invoked while model artifacts
    are missing, uninitialized, or in an unready state.
    """
    def __init__(self, detail: str = "Model artifacts are not ready or trained. Run training pipeline or wait for model initialization."):
        self.detail = detail
        self.code = "MODEL_NOT_READY"
        super().__init__(self.detail)

async def model_not_ready_exception_handler(request: Request, exc: ModelNotReadyException):
    return JSONResponse(
        status_code=503,
        content={
            "detail": exc.detail,
            "code": exc.code
        }
    )
