from fastapi import FastAPI, Depends, BackgroundTasks, status
from sqlmodel.ext.asyncio.session import AsyncSession
from contextlib import asynccontextmanager
import httpx
import logging
import os
from datetime import datetime, timezone

from .database import init_db, get_async_session
from .models import SAPIntegrationLog
from .schemas import ContractSignedWebhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrationMiddleware")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Executado no STARTUP da aplicação
    logger.info("Iniciando aplicação: Criando/verificando tabelas no Neon Postgres...")
    await init_db()
    
    yield  # A aplicação executa as rotas aqui enquanto o processo estiver ativo
    
    # Executado no SHUTDOWN da aplicação
    logger.info("Encerrando aplicação: Finalizando recursos pendentes...")

app = FastAPI(
    title="Clicksign to SAP Integration Middleware",
    description="Middleware resiliente com persistência em banco via UUIDv7 e políticas de retry",
    lifespan=lifespan
)

# Endpoint interno ou DNS do Docker para se comunicar com o Fake SAP
FAKE_SAP_URL = os.getenv("FAKE_SAP_URL", "http://localhost:8001/sap/api/v1/accounting/invoices")

async def transmit_to_sap_worker(log_id: str, company_code: str):
    """
    Trabalhador em segundo plano que gerencia seu próprio ciclo de vida de sessão 
    e tenta enviar os dados ao SAP de forma assíncrona.
    """
    # Instancia uma nova sessão isolada para o Worker em background
    async for session in get_async_session():
        log = await session.get(SAPIntegrationLog, log_id)
        if not log:
            return

        log.attempts += 1
        # CORREÇÃO: Removida chamada depreciada do datetime.utcnow()
        log.last_attempt = datetime.now(timezone.utc).replace(tzinfo=None)

        payload_sap = {
            "company_code": company_code,
            "customer_id": log.customer_id,
            "amount": log.amount,
            "contract_ref": log.contract_ref
        }

        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Tentativa {log.attempts} para enviar o Contrato {log.contract_ref} ao SAP...")
                response = await client.post(FAKE_SAP_URL, json=payload_sap, timeout=5.0)

                if response.status_code == 201:
                    data = response.json()
                    log.status = "SUCCESS"
                    log.sap_document_number = data.get("sap_document_number")
                    log.error_message = None
                    logger.info(f"Sucesso! Documento gerado no SAP: {log.sap_document_number}")
                else:
                    log.status = "FAILED"
                    log.error_message = f"SAP Erro {response.status_code}: {response.text}"
                    logger.warning(f"SAP rejeitou a requisição: {log.error_message}")

        except httpx.RequestError as exc:
            log.status = "FAILED"
            log.error_message = f"Erro de comunicação de rede: {exc}"
            logger.error(f"Falha de conexão com o SAP: {log.error_message}")

        session.add(log)
        await session.commit()
        break  # Garante a finalização do loop gerador com segurança

@app.post("/webhook/contract-signed", status_code=status.HTTP_202_ACCEPTED)
async def handle_contract_signed(
    payload: ContractSignedWebhook,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Recebe o sinal de contrato assinado, registra imediatamente no banco
    para auditoria e delega a transmissão do SAP para segundo plano.
    """
    new_log = SAPIntegrationLog(
        contract_ref=payload.contract_ref,
        customer_id=payload.customer_id,
        amount=payload.amount,
        status="PENDING"
    )
    
    session.add(new_log)
    await session.commit()
    await session.refresh(new_log)

    # MELHORIA: Simplificada a passagem de parâmetros para o worker em segundo plano
    background_tasks.add_task(
        transmit_to_sap_worker, 
        new_log.id, 
        payload.company_code
    )

    return {
        "message": "Evento recebido com sucesso. Transmissão com o SAP em andamento.",
        "integration_log_id": new_log.id,
        "status": "PROCESSING"
    }