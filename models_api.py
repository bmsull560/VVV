"""
Model Builder API endpoints for CRUD operations.
Temporary in-memory store; replace with database integration for production.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import uuid4
from datetime import datetime

router = APIRouter()

# In-memory model store
MODEL_STORE: Dict[str, dict] = {}

class ModelComponent(BaseModel):
    id: str
    type: str
    properties: dict
    position: dict
    size: Optional[dict] = None

class ModelConnection(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None

class ModelData(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    components: List[ModelComponent]
    connections: List[ModelConnection]
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    metadata: Optional[dict] = None

class SaveModelResponse(BaseModel):
    success: bool
    modelId: str
    message: Optional[str] = None

class ListModelsResponse(BaseModel):
    models: List[dict]

@router.get("/api/models", response_model=ListModelsResponse)
def list_models() -> ListModelsResponse:
    """List all models."""
    models = [
        {
            "id": m["id"],
            "name": m["name"],
            "description": m.get("description"),
            "updatedAt": m["updatedAt"],
        }
        for m in MODEL_STORE.values()
    ]
    return ListModelsResponse(models=models)

@router.get("/api/models/{model_id}", response_model=ModelData)
def get_model(model_id: str) -> ModelData:
    """Fetch a model by ID."""
    model = MODEL_STORE.get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelData(**model)

@router.post("/api/models", response_model=SaveModelResponse)
def create_model(model: ModelData) -> SaveModelResponse:
    """Create a new model."""
    model_id = str(uuid4())
    now = datetime.utcnow().isoformat()
    model_dict = model.dict()
    model_dict["id"] = model_id
    model_dict["createdAt"] = now
    model_dict["updatedAt"] = now
    MODEL_STORE[model_id] = model_dict
    return SaveModelResponse(success=True, modelId=model_id)

@router.put("/api/models/{model_id}", response_model=SaveModelResponse)
def update_model(model_id: str, model: ModelData) -> SaveModelResponse:
    """Update an existing model."""
    if model_id not in MODEL_STORE:
        raise HTTPException(status_code=404, detail="Model not found")
    now = datetime.utcnow().isoformat()
    model_dict = model.dict()
    model_dict["id"] = model_id
    model_dict["updatedAt"] = now
    MODEL_STORE[model_id] = model_dict
    return SaveModelResponse(success=True, modelId=model_id)

@router.delete("/api/models/{model_id}", response_model=SaveModelResponse)
def delete_model(model_id: str) -> SaveModelResponse:
    """
    Delete a model by ID.
    """
    if model_id not in MODEL_STORE:
        raise HTTPException(status_code=404, detail="Model not found")
    del MODEL_STORE[model_id]
    return SaveModelResponse(success=True, modelId=model_id, message="Model deleted")
