from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uuid6
import random

app = FastAPI(
    title="Fake SAP ERP SERVER",
    description="Simulador de endpoint SAP (Módulos FI/SD) para testes de integração"
)

# Schema que simulará o formato SAP para faturamento
class SAPInvoicePayLoad(BaseModel):
    company_code: str = Field(..., min_length=4, max_length=4, description="Código da empresa no SAP (ex: 'BR01')")
    customer_id: str = Field(description="ID do cliente no SAP")
    amount: float = Field(..., gt=0, description="Valor total da fatura")
    contract_ref: str = Field(description="UUID do contrato associado à fatura")

@app.post("/sap/api/v1/accounting/invoices", status_code=status.HTTP_201_CREATED)
def create_sap_invoice(payload: SAPInvoicePayLoad):
    # Simulação de instabilidade do SAP de 33%
    if random.choice([True, False, False]):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="SAP RFC Connectio Timeout: System Overloaded"
        )
    # Simulação de Sucesso: Retorna estrutura típicas do padrão SAP
    sap_documento_id = f"DOC-SAP-{random.randint(100000, 999999)}"

    return {
        "status": "SUCCESS",
        "sap_document_number": sap_documento_id,
        "contract_reference": payload.contract_ref,
        "message": f"invoice posted successfully in Company Code {payload.company_code}." 
    }