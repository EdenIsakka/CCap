from fastapi import FastAPI

from ccap.settings import Settings

settings = Settings()

# /docs y /openapi.json solo en desarrollo (STRIDE E-02).
app = FastAPI(
    title="CCap",
    docs_url="/docs" if settings.debug else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.debug else None,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
