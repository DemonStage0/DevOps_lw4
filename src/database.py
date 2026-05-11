from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, Float, DateTime, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from src.config import get_db_url  # ← исправлено

def _create_engine():
    return create_async_engine(get_db_url())

engine = _create_engine()
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Glass(Base):
    __tablename__ = "glass"
    id = Column(Integer, primary_key=True, index=True)
    RI = Column("RI", Float, nullable=False)
    Na = Column("Na", Float, nullable=False)
    Mg = Column("Mg", Float, nullable=False)
    Al = Column("Al", Float, nullable=False)
    Si = Column("Si", Float, nullable=False)
    K = Column("K", Float, nullable=False)
    Ca = Column("Ca", Float, nullable=False)
    Ba = Column("Ba", Float, nullable=False)
    Fe = Column("Fe", Float, nullable=False)
    type = Column("Type", Integer, nullable=False)

class Predict(Base):
    __tablename__ = "predict"
    id = Column(Integer, primary_key=True, index=True)
    predicted_class = Column(Integer, nullable=False)
    RI = Column("RI", Float, nullable=False)
    Na = Column("Na", Float, nullable=False)
    Mg = Column("Mg", Float, nullable=False)
    Al = Column("Al", Float, nullable=False)
    Si = Column("Si", Float, nullable=False)
    K = Column("K", Float, nullable=False)
    Ca = Column("Ca", Float, nullable=False)
    Ba = Column("Ba", Float, nullable=False)
    Fe = Column("Fe", Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

async def get_glass_data():
    async with async_session() as session:
        result = await session.execute(select(Glass))
        rows = result.scalars().all()
        X = [[r.RI, r.Na, r.Mg, r.Al, r.Si, r.K, r.Ca, r.Ba, r.Fe] for r in rows]
        y = [r.type for r in rows]
        return X, y

async def save_prediction(predicted_class: int, features: List[float]):
    async with async_session() as session:
        record = Predict(
            predicted_class=predicted_class,
            RI=features[0], Na=features[1], Mg=features[2], Al=features[3],
            Si=features[4], K=features[5], Ca=features[6], Ba=features[7], Fe=features[8],
        )
        session.add(record)
        await session.commit()