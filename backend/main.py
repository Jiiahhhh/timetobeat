from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import recommendations

app = FastAPI(title="TimeToBeat API", version="1.0.0")

# Allow frontend (Next.js) to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://timetobeat-production.up.railway.app",  # sementara
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendations.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "TimeToBeat API is running"}