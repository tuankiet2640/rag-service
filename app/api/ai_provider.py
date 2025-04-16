from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.models.schemas import AIProviderCreate, AIProviderOut
from app.models.db_models import AIProvider as AIProviderModel
from app.core.auth import get_current_admin, get_current_user
from app.db.database import get_db

router = APIRouter()

@router.get("/ai_providers", response_model=List[AIProviderOut])
async def list_ai_providers(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIProviderModel))
    providers = result.scalars().all()
    return [AIProviderOut(
        id=p.id,
        name=p.name,
        type=p.type,
        endpoint_url=p.endpoint_url,
        enabled=bool(p.enabled),
        config_json=p.config_json
    ) for p in providers]

@router.post("/ai_providers", response_model=AIProviderOut)
async def create_ai_provider(provider: AIProviderCreate, current_admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    new_provider = AIProviderModel(
        id=provider.id,
        name=provider.name,
        type=provider.type,
        endpoint_url=provider.endpoint_url,
        api_key=provider.api_key,
        enabled=1 if provider.enabled else 0,
        config_json=provider.config_json
    )
    db.add(new_provider)
    try:
        await db.commit()
        await db.refresh(new_provider)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="AI provider already exists")
    return AIProviderOut(
        id=new_provider.id,
        name=new_provider.name,
        type=new_provider.type,
        endpoint_url=new_provider.endpoint_url,
        enabled=bool(new_provider.enabled),
        config_json=new_provider.config_json
    )

@router.delete("/ai_providers/{provider_id}")
async def delete_ai_provider(provider_id: str, current_admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    provider = await db.get(AIProviderModel, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="AI provider not found")
    await db.delete(provider)
    await db.commit()
    return {"detail": "Deleted"}

@router.put("/ai_providers/{provider_id}", response_model=AIProviderOut)
async def update_ai_provider(provider_id: str, provider: AIProviderCreate, current_admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    db_provider = await db.get(AIProviderModel, provider_id)
    if not db_provider:
        raise HTTPException(status_code=404, detail="AI provider not found")
    db_provider.name = provider.name
    db_provider.type = provider.type
    db_provider.endpoint_url = provider.endpoint_url
    db_provider.api_key = provider.api_key
    db_provider.enabled = 1 if provider.enabled else 0
    db_provider.config_json = provider.config_json
    await db.commit()
    await db.refresh(db_provider)
    return AIProviderOut(
        id=db_provider.id,
        name=db_provider.name,
        type=db_provider.type,
        endpoint_url=db_provider.endpoint_url,
        enabled=bool(db_provider.enabled),
        config_json=db_provider.config_json
    )
