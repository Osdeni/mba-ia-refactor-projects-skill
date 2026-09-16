"""Relatório de vendas: agregação única no banco + regra de desconto por faixa."""
from constants import FAIXAS_DESCONTO
from models import pedido_model


def calcular_desconto(faturamento):
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0


def _quantidade(resumo, status):
    return resumo.get(status, {}).get("quantidade", 0)


def gerar():
    resumo = pedido_model.resumo_por_status()
    total_pedidos = sum(item["quantidade"] for item in resumo.values())
    faturamento = sum(item["faturamento"] for item in resumo.values())
    desconto = calcular_desconto(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": _quantidade(resumo, "pendente"),
        "pedidos_aprovados": _quantidade(resumo, "aprovado"),
        "pedidos_cancelados": _quantidade(resumo, "cancelado"),
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
