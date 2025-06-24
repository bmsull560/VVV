"""
Model Builder API endpoints for CRUD operations.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import UUID as PydanticUUID # Alias to avoid conflict with sqlalchemy.dialects.postgresql.UUID
from datetime import datetime

from sqlalchemy.orm import Session
from memory.database import get_db
from memory.database_models import Model, ModelComponent, ModelConnection

router = APIRouter()

class ModelComponentSchema(BaseModel):
    id: str
    type: str
    properties: dict
    position: dict
    size: Optional[dict] = None

class ModelConnectionSchema(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = Field(None, alias='source_handle')
    targetHandle: Optional[str] = Field(None, alias='target_handle')

    class Config:
        allow_population_by_field_name = True

class ModelDataSchema(BaseModel):
    id: Optional[PydanticUUID] = None
    name: str
    description: Optional[str] = None
    components: List[ModelComponentSchema]
    connections: List[ModelConnectionSchema]
    createdAt: Optional[datetime] = Field(None, alias='created_at')
    updatedAt: Optional[datetime] = Field(None, alias='updated_at')
    metadata: Optional[dict] = Field(None, alias='metadata_') # Alias to match ORM model

    class Config:
        orm_mode = True # Enable ORM mode for automatic conversion from ORM models
        allow_population_by_field_name = True

class SaveModelResponse(BaseModel):
    success: bool
    modelId: PydanticUUID
    message: Optional[str] = None

class ListModelsResponse(BaseModel):
    models: List[ModelDataSchema]

@router.get("/api/models", response_model=ListModelsResponse)
def list_models(db: Session = Depends(get_db)) -> ListModelsResponse:
    """List all models."""
    db_models = db.query(Model).all()
    return ListModelsResponse(models=[ModelDataSchema.from_orm(m) for m in db_models])

@router.get("/api/models/{model_id}", response_model=ModelDataSchema)
def get_model(model_id: PydanticUUID, db: Session = Depends(get_db)) -> ModelDataSchema:
    """Fetch a model by ID."""
    db_model = db.query(Model).filter(Model.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelDataSchema.from_orm(db_model)

@router.post("/api/models", response_model=SaveModelResponse)
def create_model(model: ModelDataSchema, db: Session = Depends(get_db)) -> SaveModelResponse:
    """Create a new model."""
    db_model = Model(name=model.name, description=model.description, metadata_=model.metadata)
    db.add(db_model)
    db.flush() # Flush to get the model_id

    for comp_data in model.components:
        db_component = ModelComponent(
            model_id=db_model.id,
            id=comp_data.id,
            type=comp_data.type,
            properties=comp_data.properties,
            position=comp_data.position,
            size=comp_data.size
        )
        db.add(db_component)

    for conn_data in model.connections:
        db_connection = ModelConnection(
            model_id=db_model.id,
            id=conn_data.id,
            source=conn_data.source,
            target=conn_data.target,
            source_handle=conn_data.sourceHandle,
            target_handle=conn_data.targetHandle
        )
        db.add(db_connection)

    db.commit()
    db.refresh(db_model)

    return SaveModelResponse(success=True, modelId=db_model.id)

@router.put("/api/models/{model_id}", response_model=SaveModelResponse)
def update_model(model_id: PydanticUUID, model: ModelDataSchema, db: Session = Depends(get_db)) -> SaveModelResponse:
    """Update an existing model."""
    db_model = db.query(Model).filter(Model.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")

    db_model.name = model.name
    db_model.description = model.description
    db_model.metadata_ = model.metadata
    db_model.updated_at = datetime.utcnow() # Explicitly update timestamp

    # Clear existing components and connections and add new ones
    db.query(ModelComponent).filter(ModelComponent.model_id == model_id).delete()
    db.query(ModelConnection).filter(ModelConnection.model_id == model_id).delete()
    db.flush()

    for comp_data in model.components:
        db_component = ModelComponent(
            model_id=db_model.id,
            id=comp_data.id,
            type=comp_data.type,
            properties=comp_data.properties,
            position=comp_data.position,
            size=comp_data.size
        )
        db.add(db_component)

    for conn_data in model.connections:
        db_connection = ModelConnection(
            model_id=db_model.id,
            id=conn_data.id,
            source=conn_data.source,
            target=conn_data.target,
            source_handle=conn_data.sourceHandle,
            target_handle=conn_data.targetHandle
        )
        db.add(db_connection)

    db.commit()
    db.refresh(db_model)

    return SaveModelResponse(success=True, modelId=db_model.id)

@router.delete("/api/models/{model_id}", response_model=SaveModelResponse)
def delete_model(model_id: PydanticUUID, db: Session = Depends(get_db)) -> SaveModelResponse:
    """
    Delete a model by ID.
    """
    db_model = db.query(Model).filter(Model.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")

    db.delete(db_model)
    db.commit()

    return SaveModelResponse(success=True, modelId=model_id, message="Model deleted")
