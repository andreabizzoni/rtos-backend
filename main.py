from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Guido AI",
    description="AI assistant with AG-UI integration",
    version="0.1.0",
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "guido-ai",
        }
    )
