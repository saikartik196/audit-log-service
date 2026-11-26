
from fastapi import FastAPI

app = FastAPI(
    title="Audit Log Service",
    version="0.1.0",
    description="A service for recording and verifying audit events.",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
