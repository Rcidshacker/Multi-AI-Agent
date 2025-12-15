from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import app as agent_app
from publisher import publish_to_devto

# FastAPI Server
server = FastAPI(title="AI Agent Blog Generator API")

# Enable CORS for Flutter app
server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BlogRequest(BaseModel):
    topic: str

class BlogResponse(BaseModel):
    final_blog: str
    revision_count: int
    review_feedback: str

@server.post("/generate-blog", response_model=BlogResponse)
async def generate_blog(request: BlogRequest):
    """
    Invoke the multi-agent system to generate a blog post.
    """
    inputs = {
        "topic": request.topic,
        "research_data": [],
        "blog_post": "",
        "review_feedback": "",
        "revision_count": 0
    }
    
    result = agent_app.invoke(inputs)
    
    return BlogResponse(
        final_blog=result["blog_post"],
        revision_count=result["revision_count"],
        review_feedback=result["review_feedback"]
    )

class PublishRequest(BaseModel):
    topic: str
    content: str

@server.post("/publish")
async def publish_blog(request: PublishRequest):
    """
    Manually publish the blog post to Dev.to.
    """
    url = publish_to_devto(request.topic, request.content)
    if url:
        return {"status": "success", "url": url}
    else:
        return {"status": "error", "message": "Failed to publish"}

@server.get("/health")
async def health_check():
    return {"status": "ok"}

# Alias for uvicorn
app = server
