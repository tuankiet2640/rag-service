from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from app.api import knowledge_base, query
from app.api import document
from app.api import ai_provider

app = FastAPI(title="RAG Knowledge Management Service")

# Load .env
load_dotenv()

# CORS settings from environment
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Include routers

def include_routers(app: FastAPI):
    app.include_router(knowledge_base.router, prefix="/api/v1/knowledge_bases", tags=["KnowledgeBase"])
    app.include_router(document.router, prefix="/api/v1/documents", tags=["Document"])
    app.include_router(ai_provider.router, prefix="/api/v1/ai_providers", tags=["AIProvider"])
    app.include_router(query.router, prefix="/api/v1/query", tags=["Query"])

include_routers(app)
