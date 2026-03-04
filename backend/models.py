from beanie import Document, Indexed
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Literal
import uuid
from datetime import datetime

class User(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    email: Indexed(EmailStr, unique=True)
    password_hash: str
    role: Literal["student", "teacher"]
    name: str

    class Settings:
        name = "users"

# --- Rubric Models ---

class RubricLevel(BaseModel):
    level_name: str  # e.g., "Excellent", "Fair"
    score: float
    description: str

class RubricCriterion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    max_points: float
    description: str
    levels: List[RubricLevel]

class Rubric(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str
    criteria: List[RubricCriterion]

    class Settings:
        name = "rubrics"

# --- Submission & Reference Models ---

class Assignment(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    title: str
    rubric_id: str
    reference_material_ids: List[str] = []

    class Settings:
        name = "assignments"

class ReferenceMaterial(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    filename: str
    content_type: str
    text_content: str # Extracted text

    class Settings:
        name = "reference_materials"

class StudentSubmission(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    assignment_id: str
    student_id: str
    filename: str
    text_content: str
    submission_date: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "submissions"

# --- Feedback Output Models ---

class Citation(BaseModel):
    text_snippet: str
    page_num: Optional[int] = None
    comment: Optional[str] = None

class CriterionFeedback(BaseModel):
    criterion_id: str
    name: str
    score: float
    max_points: float
    level_achieved: str
    reasoning: str
    evidence_quotes: List[str] = []

class FeedbackResponse(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    submission_id: str
    total_score: float
    max_score: float
    criteria_feedback: List[CriterionFeedback]
    general_summary: str
    strengths: List[str]
    weaknesses: List[str]
    improvement_plan: Optional[List[Dict[str, str]]] = None # Matches improvement prompt output
    status: Literal["draft", "approved", "published"] = "draft"

    class Settings:
        name = "feedbacks"

