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

SECRET_KEY = "b2bvalue-secret-key"  # Use env var in production
ALGORITHM = "HS256"

app = FastAPI(title="B2BValue API", description="API for B2BValue GTM Platform", version="1.0.0")
logger = logging.getLogger(__name__)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory user store (demo only) ---
users_db = {"demo-user": {"username": "demo-user", "password": "demo-pass"}}

# --- JWT Auth ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None or username not in users_db:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        return users_db[username]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication")

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
@app.post("/api/register")
def register(user: UserRegister):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    users_db[user.username] = {"username": user.username, "password": user.password}
    return {"message": "Registered successfully"}

@app.post("/api/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

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
