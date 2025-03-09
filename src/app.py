from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="EyeSmile API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "service": "EyeSmile API"}

@app.get("/api/v1/endpoints")
async def list_endpoints():
    return {
        "endpoints": [
            {"path": "/api/v1/health", "method": "GET"},
            {"path": "/api/v1/users/profile", "method": "POST"},
            {"path": "/api/v1/face-analysis", "method": "POST"},
        ]
    } 