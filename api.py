from fastapi import FastAPI, HTTPException, Security, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add services directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from services.agent import generate_chat_response

# Security Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS").split(",")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))  # More generous for public use
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PUBLIC_MODE = os.getenv("PUBLIC_MODE", "true").lower() == "true"  # No API key required

# Rate limiting storage (per IP address)
rate_limit_storage = defaultdict(list)
rate_limit_lock = threading.Lock()

app = FastAPI(
    title="Neckarmedia Chatbot API", 
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,
)

# Enable CORS with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

class ChatRequest(BaseModel):
    user_prompt: str
    
class ChatResponse(BaseModel):
    response: str

# Security Functions

def check_rate_limit(request: Request) -> None:
    """Check if request exceeds rate limit."""
    # Use client IP or API key as identifier
    client_id = request.client.host if request.client else "unknown"
    
    with rate_limit_lock:
        current_time = datetime.now()
        # Clean old entries
        rate_limit_storage[client_id] = [
            timestamp for timestamp in rate_limit_storage[client_id]
            if current_time - timestamp < timedelta(seconds=RATE_LIMIT_PERIOD)
        ]
        
        # Check if rate limit exceeded
        if len(rate_limit_storage[client_id]) >= RATE_LIMIT_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_PERIOD} seconds."
            )
        
        # Add current request
        rate_limit_storage[client_id].append(current_time)

# Middleware for security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
    
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Neckarmedia Chatbot API", 
        "version": "1.0.0",
        "endpoints": {
            "/chat_response": "POST - Send a user prompt and get AI response",
            "/health": "GET - Check API health status"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Neckarmedia Chatbot API"}

@app.post("/chat_response", response_model=ChatResponse)
async def chat_response(
    chat_request: ChatRequest,
    http_request: Request
):
    """
    Main chat endpoint that triggers the agentic workflow.
    Public endpoint with rate limiting protection.
    
    Args:
        chat_request: ChatRequest containing the user_prompt
        http_request: FastAPI Request object for rate limiting
        
    Returns:
        ChatResponse with the AI-generated response
    """
    try:
        # Check rate limit
        check_rate_limit(http_request)
        
        # Validate input
        if not chat_request.user_prompt or not chat_request.user_prompt.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="user_prompt cannot be empty"
            )
        
        # Additional input validation
        if len(chat_request.user_prompt) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_prompt too long (max 5000 characters)"
            )
        
        # Trigger the agentic workflow
        response_text = generate_chat_response(chat_request.user_prompt)
        
        return ChatResponse(response=response_text)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in chat_response endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error" if ENVIRONMENT == "production" else f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

