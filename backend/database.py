from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models import Assignment, Rubric, StudentSubmission, FeedbackResponse, ReferenceMaterial, User
import os

async def init_db():
    # Connect to MongoDB (default local instance, override with env var in production)
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_uri)
    
    # Initialize Beanie with the 'smart_feedback_db' database and our document models
    await init_beanie(database=client.smart_feedback_db, document_models=[
        Assignment,
        Rubric,
        StudentSubmission,
        FeedbackResponse,
        ReferenceMaterial,
        User
    ])
