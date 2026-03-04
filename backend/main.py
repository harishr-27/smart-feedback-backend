from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List
from models import Assignment, Rubric, StudentSubmission, FeedbackResponse, ReferenceMaterial, RubricCriterion
from feedback_service import FeedbackService
from rag_service import RAGService
from utils import extract_text_from_file
import uuid
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from pydantic import BaseModel, EmailStr
from auth_service import get_password_hash, verify_password, create_access_token, decode_access_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, status
from models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await User.find_one(User.email == payload.get("sub"))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str # "student" or "teacher"

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: str
    name: str
    email: str

app = FastAPI(title="Smart Feedback Generator API")


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup Event to Connect to DB
@app.on_event("startup")
async def start_db():
    await init_db()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Global Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )

feedback_service = FeedbackService()
rag_service = RAGService()

@app.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await User.find_one(User.email == user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create User
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role,
        name=user_data.name
    )
    await user.create()
    
    # Create Token
    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": str(user.id)})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": user.role, 
        "user_id": str(user.id), 
        "name": user.name,
        "email": user.email
    }

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.find_one(User.email == form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": str(user.id)})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": user.role, 
        "user_id": str(user.id), 
        "name": user.name,
        "email": user.email
    }


@app.post("/assignments/", response_model=Assignment)
async def create_assignment(assignment: Assignment, current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create assignments")
    await assignment.create()
    return assignment

@app.get("/assignments/", response_model=List[Assignment])
async def list_assignments():
    return await Assignment.find_all().to_list()

@app.post("/rubrics/", response_model=Rubric)
async def upload_rubric(rubric: Rubric, current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create rubrics")
    await rubric.create()
    return rubric

@app.post("/reference-materials/{assignment_id}")
async def upload_reference(
    assignment_id: str, 
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can upload reference material")

    # Find assignment by ID
    assignment = await Assignment.get(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    content = await file.read()
    text = extract_text_from_file(content, file.filename)
    
    ref_mat = ReferenceMaterial(
        filename=file.filename,
        content_type=file.content_type,
        text_content=text
    )
    
    # Save Reference Material
    await ref_mat.create()
    
    # Ingest into RAG (Sync/Async needs care, RAGService is currently Sync, keeping it as is for now)
    rag_service.ingest_reference_material(ref_mat)
    
    # Link to assignment
    assignment.reference_material_ids.append(ref_mat.id)
    await assignment.save()
    
    return {"message": "Reference material ingested", "id": ref_mat.id}

from fastapi import BackgroundTasks

# ... (imports)

async def generate_feedback_task(submission_id: str, rubric_id: str):
    """
    Background task to generate feedback and update the submission.
    """
    try:
        submission = await StudentSubmission.get(submission_id)
        rubric = await Rubric.get(rubric_id)
        
        if submission and rubric:
            print(f"⏳ Background Task: Generating feedback for {submission_id}...")
            feedback = await feedback_service.generate_feedback(submission, rubric)
            
            # Save feedback
            await feedback.create()
            print(f"✅ Background Task: Feedback generated for {submission_id}")
            
    except Exception as e:
        print(f"❌ Background Task Error: {e}")

@app.post("/submissions/{assignment_id}", response_model=StudentSubmission)
async def submit_and_grade(
    assignment_id: str, 
    student_id: str, 
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    assignment = await Assignment.get(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    rubric = await Rubric.get(assignment.rubric_id)
    if not rubric:
         raise HTTPException(status_code=404, detail="Rubric not found")
    
    # Process File
    content = await file.read()
    text = extract_text_from_file(content, file.filename)
    
    submission = StudentSubmission(
        assignment_id=assignment_id,
        student_id=student_id,
        filename=file.filename,
        text_content=text
    )
    
    await submission.create()
    
    # Trigger Feedback Generation in Background
    background_tasks.add_task(generate_feedback_task, submission.id, rubric.id)
    
    # Return Submission immediately (Frontend will poll for feedback)
    return submission

@app.get("/submissions/", response_model=List[StudentSubmission])
async def list_submissions():
    return await StudentSubmission.find_all().to_list()

@app.get("/feedbacks/", response_model=List[FeedbackResponse])
async def list_feedbacks():
    return await FeedbackResponse.find_all().to_list()

@app.get("/")
async def root():
    return {"message": "Smart Feedback Generator API is running with MongoDB"}



