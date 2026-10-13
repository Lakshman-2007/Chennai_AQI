"""
Custom Exceptions and Structured Exception Handlers for Chennai Air Quality Framework.
Conforms to PRD v2.3 Section 3 & 5: Decoupled readiness, standard error schema.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

class ModelNotReadyException(Exception):
    """
    Raised when core prediction endpoints are invoked while model artifacts
    are missing, uninitialized, or in an unready state.
    """
    def __init__(self, detail: str = "Prediction service unavailable: core model artifacts not ready.", code: str = "MODEL_NOT_READY"):
        self.detail = detail
        self.code = code
        super().__init__(self.detail)

class ExplainerNotReadyException(Exception):
    """
    Raised when XAI explanation endpoints are invoked while the explainer artifact
    is missing, uninitialized, or in an unready state.
    Does NOT block core prediction capabilities.
    """
    def __init__(self, detail: str = "XAI explainer service unavailable: explainer artifact not ready.", code: str = "EXPLAINER_NOT_READY"):
        self.detail = detail
        self.code = code
        super().__init__(self.detail)

async def model_not_ready_exception_handler(request: Request, exc: ModelNotReadyException):
    return JSONResponse(
        status_code=503,
        content={
            "detail": exc.detail,
            "code": exc.code,
            "error": {
                "code": exc.code,
                "message": exc.detail,
                "retryable": False
            }
        }
    )

async def explainer_not_ready_exception_handler(request: Request, exc: ExplainerNotReadyException):
    return JSONResponse(
        status_code=503,
        content={
            "detail": exc.detail,
            "code": exc.code,
            "error": {
                "code": exc.code,
                "message": exc.detail,
                "retryable": False
            }
        }
    )
