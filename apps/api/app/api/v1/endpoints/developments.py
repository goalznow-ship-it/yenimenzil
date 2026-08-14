from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies.auth import require_roles
from app.db.session import get_db
from app.models.development import ComplexUnitType, Developer, ResidentialComplex
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.development import ComplexCreate, ComplexRead, ComplexUpdate, DeveloperCreate, DeveloperRead

router = APIRouter(prefix="/developments", tags=["residential-complexes"])
staff = require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)


def _complex_query():
    return select(ResidentialComplex).options(
        selectinload(ResidentialComplex.developer),
        selectinload(ResidentialComplex.unit_types),
    )


@router.get("/developers", response_model=list[DeveloperRead])
async def list_developers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Developer).order_by(Developer.is_verified.desc(), Developer.name))
    return list(result.scalars().all())


@router.post("/developers", response_model=DeveloperRead, status_code=status.HTTP_201_CREATED)
async def create_developer(payload: DeveloperCreate, _: User = Depends(staff), db: AsyncSession = Depends(get_db)):
    developer = Developer(**payload.model_dump())
    db.add(developer)
    await db.commit()
    await db.refresh(developer)
    return developer


@router.get("/complexes", response_model=list[ComplexRead])
async def list_complexes(
    q: str | None = None,
    city: str | None = None,
    featured: bool | None = None,
    limit: int = Query(default=48, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = _complex_query().where(ResidentialComplex.is_published.is_(True))
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(ResidentialComplex.name.ilike(term), ResidentialComplex.address.ilike(term)))
    if city:
        stmt = stmt.where(ResidentialComplex.city == city)
    if featured is not None:
        stmt = stmt.where(ResidentialComplex.is_featured.is_(featured))
    stmt = stmt.order_by(ResidentialComplex.is_featured.desc(), ResidentialComplex.created_at.desc()).offset(offset).limit(limit)
    return list((await db.execute(stmt)).scalars().unique().all())


@router.get("/complexes/{slug}", response_model=ComplexRead)
async def get_complex(slug: str, db: AsyncSession = Depends(get_db)):
    item = (await db.execute(_complex_query().where(ResidentialComplex.slug == slug, ResidentialComplex.is_published.is_(True)))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Residential complex not found")
    return item


@router.get("/admin/complexes", response_model=list[ComplexRead])
async def admin_list_complexes(_: User = Depends(staff), db: AsyncSession = Depends(get_db)):
    return list((await db.execute(_complex_query().order_by(ResidentialComplex.created_at.desc()))).scalars().unique().all())


@router.post("/complexes", response_model=ComplexRead, status_code=status.HTTP_201_CREATED)
async def create_complex(payload: ComplexCreate, _: User = Depends(staff), db: AsyncSession = Depends(get_db)):
    data = payload.model_dump(exclude={"unit_types"})
    item = ResidentialComplex(**data)
    item.unit_types = [ComplexUnitType(**unit.model_dump()) for unit in payload.unit_types]
    db.add(item)
    await db.commit()
    result = await db.execute(_complex_query().where(ResidentialComplex.id == item.id))
    return result.scalar_one()


@router.patch("/complexes/{complex_id}", response_model=ComplexRead)
async def update_complex(complex_id: uuid.UUID, payload: ComplexUpdate, _: User = Depends(staff), db: AsyncSession = Depends(get_db)):
    item = await db.get(ResidentialComplex, complex_id)
    if not item:
        raise HTTPException(status_code=404, detail="Residential complex not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    result = await db.execute(_complex_query().where(ResidentialComplex.id == item.id))
    return result.scalar_one()


@router.delete("/complexes/{complex_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_complex(complex_id: uuid.UUID, _: User = Depends(staff), db: AsyncSession = Depends(get_db)):
    item = await db.get(ResidentialComplex, complex_id)
    if not item:
        raise HTTPException(status_code=404, detail="Residential complex not found")
    await db.delete(item)
    await db.commit()
