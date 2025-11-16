# src/models/formatter.py

"""
Formatadores de resposta para o Condo Package Scanner.
Esses formatadores NÃO incluem 'status' — isso é responsabilidade da rota.
"""

import traceback
from typing import Dict, Optional

def format_success_result(names_with_units: Optional[Dict[str, dict]] = None,
                          reason: Optional[str] = None) -> dict:
    """
    Retorna um formato padronizado para todos os cenários de sucesso.
    - names_with_units: dict{name: {apartment, block}, ...}, vazio se nenhum nome
    - reason: mensagem explicando por que nenhum candidato foi validado
    """
    names_with_units = names_with_units or {}
    return {
        "candidates": len(names_with_units),
        "names_with_units_info": names_with_units,
        "reason": reason
    }


def format_error_result(error_message: Exception) -> dict:
    """
    Erro interno no processamento.
    (Status será adicionado pela rota.)
    """
    tb = traceback.format_exc()
    tb = tb.replace("\n", " ")
    return {
        "message": str(error_message),
        "traceback": tb
    }
