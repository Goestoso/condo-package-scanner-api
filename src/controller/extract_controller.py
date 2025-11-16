"""
Módulo que realiza a extração das informações das encomendas:
1. Extrai texto da imagem via OCR
2. Identifica candidatos a nomes (NER)
3. Sanitiza e valida nomes usando banco + fuzzy
4. Extrai endereço (pode ter lógica similar)
"""

from pathlib import Path
from io import BytesIO
from src.extractor import Extractor
from src.utils.validators import (
    validate_recipient_name_candidates,
    validate_recipient_name_by_unit,
    validate_recipient_name_by_apartment,
    validate_recipient_name_by_block,
    fill_missing_unit_info,
)
from src.models.formatter import format_success_result, format_error_result
from src.utils.normalize import normalize_block
from src.utils.sanitize import sanitize_name_cand
from src.utils.logger import get_logger

logger = get_logger(__name__)

def extract_package_info_controller(image_input):
    """
    Processa uma imagem (caminho ou bytes) e retorna o resultado padronizado da extração.
    """
    try:
        # --- Instancia Extractor ---
        if isinstance(image_input, (str, Path)):
            extractor = Extractor(image_input)
        elif isinstance(image_input, (bytes, BytesIO)):
            extractor = Extractor(image_input, in_memory=True)
        else:
            raise TypeError("Parâmetro inválido: esperado caminho (str) ou bytes de imagem.")

        # --- OCR ---
        extractor.extract_text()

        # --- Extrai candidatos a nomes ---
        extractor.extract_recipient_name()
        candidates = extractor.candidates_name
        sanitized_candidates = {sanitize_name_cand(c) for c in candidates if sanitize_name_cand(c)}

        # Nenhum candidato de nome
        if not sanitized_candidates:
            return format_success_result(names_with_units={}, reason="Nenhum candidato de nome válido encontrado na etiqueta.")

        # --- Endereço e unidade ---
        extractor.extract_recipient_address()
        unit_info = extractor.extract_apartment_and_block() or {"apartment": None, "block": None}
        unit_info["block"] = normalize_block(unit_info["block"])

        # --- Validação ---
        if unit_info.get("apartment") and unit_info.get("block"):
            validated_names = validate_recipient_name_by_unit(unit_info, sanitized_candidates)
            names_with_units = {name: dict(unit_info) for name in validated_names}
        elif unit_info.get("apartment"):
            validated_names = validate_recipient_name_by_apartment(unit_info["apartment"], sanitized_candidates)
            names_with_units = {name: {"apartment": unit_info["apartment"], "block": None} for name in validated_names}
        elif unit_info.get("block"):
            validated_names = validate_recipient_name_by_block(unit_info["block"], sanitized_candidates)
            names_with_units = {name: {"apartment": None, "block": unit_info["block"]} for name in validated_names}
        else:
            validated_names, names_with_units = validate_recipient_name_candidates(sanitized_candidates)

        # Nenhum nome validado
        if not validated_names:
            return format_success_result(names_with_units={}, reason="Nenhum nome validado no banco de dados.")

        # --- Preenche unidades faltantes ---
        for name in validated_names:
            names_with_units[name] = fill_missing_unit_info(name, names_with_units[name])

        # --- Retorno padronizado ---
        return format_success_result(names_with_units=names_with_units, reason= "Candidatos com nomes similares validados no banco de dados" if len(validated_names) > 1  else "Candidato único validado no banco de dados")

    except Exception as e:
        logger.exception(f"Erro inesperado durante a extração: {e}")
        return format_error_result(e)
