from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import AsyncGenerator
from dotenv import load_dotenv
import os

load_dotenv()

# CORREÇÃO: Ajustado de "DABASE_URL" para "DATABASE_URL"
RAW_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/clicksign_sap"
)

# Adaptação necessária para o driver assíncrono Psycopg 3 para funcionar com o Neon
if RAW_DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = RAW_DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    DATABASE_URL = RAW_DATABASE_URL

# Cria uma engine e passa uma connect_args para garantir suporte a SSL da Neon
async_engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    pool_pre_ping=True,
    pool_recycle=60,
    connect_args={"sslmode": "require"} if "neon" in DATABASE_URL else {}
)

async def init_db():
    async with async_engine.begin() as conn:
        from .models import SAPIntegrationLog
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    
    async_session_factory = async_sessionmaker(
        async_engine, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session