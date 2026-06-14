from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
import uuid6
from typing import Optional

"""
Simulando uma tabela que precisaria registrar as tentativas de envio para o SAP.
Se o SAP falhar, o status fica em PENDING para o mecanismo de retry processar depois.
"""

class SAPIntegrationLog(SQLModel, table=True):
    __tablename__ = "sap_integration_log"

    id: str = Field(
        default_factory=lambda: str(uuid6.uuid7()), 
        primary_key=True,
        description="UUIDv7 ordenado por tempo - Otimizado para B-Tree"
    )
    contract_ref: str = Field(index=True, description="ID do contrato")
    customer_id: str
    amount: float
    status: str = Field(default="PENDING", description="PENDING, SUCCESS, FAILED")
    sap_document_number: Optional[str] = Field(default=None)
    attempts: int = Field(default=0)
    
    # Solução moderna para substituir o datetime.utcnow() mantendo compatibilidade com TIMESTAMP naive
    last_attempt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        description="Data e hora da última tentativa em UTC"
    )
    error_message: Optional[str] = Field(default=None)