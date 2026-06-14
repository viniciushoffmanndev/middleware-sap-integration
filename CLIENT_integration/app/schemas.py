from pydantic import BaseModel, Field, ConfigDict

"""
Payload que o Middleware irá receber.
Pense no webhook avisando que o contrato foi assinado, e o Middleware precisa enviar os dados para o SAP.
"""

class ContractSignedWebhook(BaseModel):
    contract_ref: str = Field(..., description="ID do contrato assinado")
    customer_id: str = Field(..., description="ID do cliente associado ao contrato")
    amount: float = Field(..., gt=0, description="Valor do faturamento") # Maior que zero
    company_code: str = Field(default="BR01", min_length=4, max_length=4, description="Código da empresa no SAP")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "contract_ref": "c4b1a829-9dc4-4d1a-8533-87a1122a2026",
                "customer_id": "CUST-9901",
                "amount": 1500.75,
                "company_code": "BR01"
            }
        }
    )