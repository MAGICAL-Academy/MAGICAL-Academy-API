from fastapi import HTTPException, Depends, FastAPI, Request
import logging
from APILogger import APILogger
from ApiKey import get_api_key
from block_path import blocked_paths
from routers.Assitant import router as assistant_router
from routers.story_router import story_router

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
app = FastAPI()

# Health Check Endpoint (no API key required)
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Include your routers with the API key dependency
# app.include_router(content_router, prefix="/content", tags=["Content"], dependencies=[Depends(get_api_key)])
# app.include_router(completion_router, prefix="/completion", tags=["Completion"], dependencies=[Depends(get_api_key)])
# app.include_router(audio_router, prefix="/audio", tags=["Audio"], dependencies=[Depends(get_api_key)])
app.include_router(story_router, prefix="/story", tags=["story"], dependencies=[Depends(get_api_key)])
# app.include_router(assistant_router, prefix="/assistant", tags=["Assistant"], dependencies=[Depends(get_api_key)])
# app.include_router(GoogleGenerativeAI_router, prefix="/GoogleGenerativeAI", tags=["GoogleGenerativeAI"], dependencies=[Depends(get_api_key)])

app_logger = APILogger("app")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 Templates
templates = Jinja2Templates(directory="templates")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    return await app_logger.log_request(request, call_next)

@app.middleware("http")
async def block_404_requests(request: Request, call_next):
    if request.url.path in blocked_paths:
        raise HTTPException(status_code=403, detail="Forbidden")
    response = await call_next(request)
    return response

# Main function to run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
