from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CMT Poster Generator",
    description="API for generating CMT meeting posters",
    version="1.0.0"
)

# Configure CORS for Power Automate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "CMT Poster Generator API",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "cmt-poster-generator"}

@app.post("/generate-posters")
def generate_posters():
    return {"message": "Poster generation endpoint - coming soon!"}
