import asyncio
import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from memory.core import MemoryManager
from memory.types import KnowledgeEntity, MemoryTier
from datetime import datetime, timedelta, timezone
import uuid
import jwt

from agents.core.agent_base import AgentStatus
from agents.value_driver.main import ValueDriverAgent
from agents.persona.main import PersonaAgent
from agents.roi_calculator.main import ROICalculatorAgent
from agents.sensitivity_analysis.main import SensitivityAnalysisAgent
from agents.progress_tracking.main import ProgressTrackingAgent

import os
import asyncpg # For PostgreSQL
from passlib.context import CryptContext # For password hashing

# --- Environment Variables & Configuration --- 
SECRET_KEY: str = os.environ.get("B2BVALUE_SECRET_KEY")
ALGORITHM: str = "HS256"
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable 'B2BVALUE_SECRET_KEY' must be set for secure operation. See deployment docs.")

# Database Configuration
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB")

if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
    raise RuntimeError("Database environment variables (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB) must be set. See deployment docs.")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI Application Instance
app = FastAPI(title="B2BValue API", description="API for B2BValue GTM Platform", version="1.0.0")

# --- Database Connection Pool --- 
db_pool: Optional[asyncpg.Pool] = None

async def get_db_pool() -> asyncpg.Pool:
    if db_pool is None:
        raise RuntimeError("Database pool not initialized.")
    return db_pool

@app.on_event("startup")
async def startup_db_client():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        logger.info("Database connection pool established.")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        # Depending on policy, you might want to raise an error here to stop startup
        # For now, we log and db_pool will remain None, causing issues later.
        # Consider a retry mechanism or a hard stop.

@app.on_event("shutdown")
async def shutdown_db_client():
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed.")

logger = logging.getLogger(__name__)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- JWT Auth ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data (dict): Data to encode in token.
        expires_delta (Optional[timedelta]): Token expiry.

    Returns:
        str: Encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- Password & User Helper Functions ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)

async def get_user_from_db(db: asyncpg.Pool, username: str) -> Optional[UserInDB]:
    """Retrieve a user from the database by username."""
    row = await db.fetchrow("SELECT id, username, hashed_password, created_at, updated_at FROM users WHERE username = $1", username)
    return UserInDB(**row) if row else None

async def get_current_user(token: str = Depends(oauth2_scheme), db: asyncpg.Pool = Depends(get_db_pool)) -> User:
    """
    Retrieve current authenticated user from JWT token and database.

    Args:
        token (str): JWT token from request.
        db (asyncpg.Pool): Database connection pool.

    Returns:
        User: Authenticated user object.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await get_user_from_db(db, username=username)
    if user is None:
        raise credentials_exception
    return User.model_validate(user) # Pydantic v2
    # return User.from_orm(user) # Pydantic v1

# --- Memory Manager ---
memory_manager = MemoryManager()
memory_manager.initialize()

# --- Agent Instantiation ---
agent_config = {}
mock_mcp_client = None
value_driver_agent = ValueDriverAgent("value_driver_agent", mock_mcp_client, agent_config)
persona_agent = PersonaAgent("persona_agent", mock_mcp_client, agent_config)
roi_calculator_agent = ROICalculatorAgent("roi_calculator_agent", mock_mcp_client, agent_config)
sensitivity_analysis_agent = SensitivityAnalysisAgent("sensitivity_analysis_agent", mock_mcp_client, agent_config)
progress_tracking_agent = ProgressTrackingAgent("progress_tracking_agent", mock_mcp_client, agent_config)

# --- Pydantic Schemas ---
class KnowledgeEntityIn(BaseModel):
    content: str
    content_type: str
    creator_id: str
    sensitivity: Optional[str] = None

class KnowledgeEntityOut(BaseModel):
    id: str
    content: str
    content_type: str
    creator_id: str
    created_at: datetime
    updated_at: datetime
    sensitivity: Optional[str]
    tier: str

class UserRegister(BaseModel):
    username: str
    password: str

class User(BaseModel): # For API responses (no password)
    id: uuid.UUID
    username: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserInDB(User): # Internal representation, includes hashed_password
    hashed_password: str

# --- Pydantic Schemas for Interactive Calculator ---
class DiscoveryRequest(BaseModel):
    text: str

class Tier3Metric(BaseModel):
    name: str
    type: str
    default_value: float
    value: Optional[float] = None

class Tier2Driver(BaseModel):
    name: str
    description: str
    tier_3_metrics: List[Tier3Metric]

class ValueDriverPillar(BaseModel):
    pillar: str
    tier_2_drivers: List[Tier2Driver]

class QuantifyRequest(BaseModel):
    drivers: List[ValueDriverPillar]
    investment: float

class SensitivityVariation(BaseModel):
    tier_2_driver_name: str
    tier_3_metric_name: str
    percentage_changes: List[float]

class SensitivityRequest(BaseModel):
    drivers: List[ValueDriverPillar]
    investment: float
    variations: List[SensitivityVariation]

class ProgressRequest(BaseModel):
    current_stage: str

# --- Auth Endpoints ---
@app.post("/api/register", response_model=User)
async def register(user_data: UserRegister, db: asyncpg.Pool = Depends(get_db_pool)):
    """Register a new user."""
    existing_user = await get_user_from_db(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user_data.password)
    try:
        # Ensure gen_random_uuid() is available or use uuid.uuid4()
        # The migration script adds pgcrypto for gen_random_uuid()
        saved_user_row = await db.fetchrow(
            "INSERT INTO users (username, hashed_password) VALUES ($1, $2) RETURNING id, username, created_at, updated_at",
            user_data.username, hashed_password
        )
        if not saved_user_row:
            raise HTTPException(status_code=500, detail="Could not create user")
        return User(**saved_user_row)
    except asyncpg.exceptions.UniqueViolationError: # Catch race condition if user was just created
        raise HTTPException(status_code=400, detail="Username already registered")
    except Exception as e:
        logger.error(f"Error during user registration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during registration")

@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: asyncpg.Pool = Depends(get_db_pool)):
    """Log in an existing user."""
    user = await get_user_from_db(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(hours=1) # Or from config
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Interactive Calculator Endpoints ---
@app.post("/api/discover-value")
async def discover_value(req: DiscoveryRequest, user=Depends(get_current_user)):
    try:
        value_driver_task = value_driver_agent.execute({'text': req.text})
        persona_task = persona_agent.execute({'text': req.text})
        results = await asyncio.gather(value_driver_task, persona_task)
        value_driver_result, persona_result = results[0], results[1]

        if value_driver_result.status == AgentStatus.FAILED or persona_result.status == AgentStatus.FAILED:
            raise HTTPException(status_code=500, detail="Agent execution failed.")

        return {
            "value_drivers": value_driver_result.data,
            "personas": persona_result.data
        }
    except Exception as e:
        logger.error(f"Error in discover-value endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quantify-roi")
async def quantify_roi(req: QuantifyRequest, user=Depends(get_current_user)):
    try:
        input_data = req.dict()
        result = await roi_calculator_agent.execute(input_data)
        if result.status == AgentStatus.FAILED:
            raise HTTPException(status_code=400, detail=result.data.get("error", "ROI calculation failed."))
        return result.data
    except Exception as e:
        logger.error(f"Error in quantify-roi endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-sensitivity")
async def analyze_sensitivity(req: SensitivityRequest, user=Depends(get_current_user)):
    try:
        input_data = req.dict()
        result = await sensitivity_analysis_agent.execute(input_data)
        if result.status == AgentStatus.FAILED:
            raise HTTPException(status_code=400, detail=result.data.get("error", "Sensitivity analysis failed."))
        return result.data
    except Exception as e:
        logger.error(f"Error in analyze-sensitivity endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/progress")
async def get_progress(req: ProgressRequest, user=Depends(get_current_user)):
    try:
        result = await progress_tracking_agent.execute(req.dict())
        if result.status == AgentStatus.FAILED:
            raise HTTPException(status_code=400, detail=result.data.get("error", "Progress tracking failed."))
        return result.data
    except Exception as e:
        logger.error(f"Error in progress endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Legacy API Endpoints ---
@app.post("/api/start-analysis")
async def start_analysis(entity: KnowledgeEntityIn, user=Depends(get_current_user)):
    entity_obj = KnowledgeEntity(
        id=str(uuid.uuid4()),
        content=entity.content,
        content_type=entity.content_type,
        creator_id=entity.creator_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        sensitivity=entity.sensitivity,
        tier=MemoryTier.SEMANTIC,
    )
    entity_id = await memory_manager.store(entity_obj, user_id=entity.creator_id)
    return {"id": entity_id}

@app.get("/api/analysis-progress/{id}")
async def get_analysis_progress(id: str, user=Depends(get_current_user)):
    return {"id": id, "progress": 100, "status": "complete"}

@app.get("/api/analysis-results/{id}")
async def get_analysis_results(id: str, user=Depends(get_current_user)):
    entity = await memory_manager.retrieve(id, tier=MemoryTier.SEMANTIC)
    if not entity:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return entity.to_dict()

# --- Deployment Notes ---
# Run with: uvicorn b2bvalue-api.main:app --reload
# Use a production server (gunicorn/uvicorn) and secure SECRET_KEY in production

"""
SECURITY NOTICE:
- The SECRET_KEY is now loaded from the environment variable 'B2BVALUE_SECRET_KEY'.
- Never commit secrets to source control. Set this variable securely in your deployment environment.
- See deployment documentation for secure secret management practices.
"""
