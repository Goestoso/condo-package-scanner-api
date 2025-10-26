"""
Módulo principal que centraliza a lógica do programa:
1. Extrai texto da imagem via OCR
2. Identifica candidatos a nomes (NER)
3. Sanitiza e valida nomes usando banco + fuzzy
4. Extrai endereço (pode ter lógica similar)
"""

from pathlib import Path
from src.extractor import Extractor
from src.utils.validators import (
    validate_recipient_name_candidates,
    validate_recipient_name_by_unit,
    validate_recipient_name_by_apartment,
    validate_recipient_name_by_block,
    fill_missing_unit_info,
)
from src.utils.normalize import normalize_block
from src.utils.sanitize import sanitize_name_cand
from src.utils.logger import get_logger
from io import BytesIO
from PIL import Image


logger = get_logger(__name__)

def main(image_input):
    """
    Processa uma imagem (caminho ou bytes) e retorna o resultado da extração.
    """
    try:
        # --- 1. Instancia o Extractor ---
        if isinstance(image_input, (str, Path)):
            logger.info(f"Iniciando extração da imagem: {image_input}")
            extractor = Extractor(image_input)
        elif isinstance(image_input, (bytes, BytesIO)):
            logger.info("Iniciando extração da imagem (em memória).")
            extractor = Extractor(image_input, in_memory=True)
        else:
            raise TypeError("Parâmetro inválido: esperado caminho (str) ou bytes de imagem.")

        # --- 2. OCR ---
        extractor.extract_text()
        logger.info("OCR concluído.")
        
        # --- 3. Extrai candidatos a nomes (NER) ---
        extractor.extract_recipient_name()
        candidates = extractor.candidates_name

        # --- 3.1. Sanitiza os candidatos ---
        sanitized_candidates = {sanitize_name_cand(c) for c in candidates if sanitize_name_cand(c)}
        logger.debug(f"Candidatos a nomes sanitizados: {sanitized_candidates}")

        # 🧩 Caso não haja candidatos válidos
        if not sanitized_candidates:
            logger.warning("Nenhum candidato de nome válido encontrado nas etiquetas (NER vazio ou nomes inválidos).")
            result = {
                "names": [],
                "unit_info": {"apartment": None, "block": None}
            }
            logger.info(f"Extração completa: {result}")
            return result

        # --- 4. Extrai endereço ---
        extractor.extract_recipient_address()
        address = extractor.candidates_address
        logger.debug(f"Endereço extraído: {address}")

        # --- 5. Extrai ap/bloco ---
        unit_info = extractor.extract_apartment_and_block() or {"apartment": None, "block": None}
        unit_info["block"] = normalize_block(unit_info["block"])

        # --- 6. Valida nomes ---
        if unit_info.get("apartment") and unit_info.get("block"):
            validated_names = validate_recipient_name_by_unit(unit_info, sanitized_candidates)
            names_with_units = {name: unit_info for name in validated_names}
        elif unit_info.get("apartment"):
            validated_names = validate_recipient_name_by_apartment(unit_info["apartment"], sanitized_candidates)
            names_with_units = {name: {"apartment": unit_info["apartment"], "block": None} for name in validated_names}
        elif unit_info.get("block"):
            validated_names = validate_recipient_name_by_block(unit_info["block"], sanitized_candidates)
            names_with_units = {name: {"apartment": None, "block": unit_info["block"]} for name in validated_names}
        else:
            validated_names, names_with_units = validate_recipient_name_candidates(sanitized_candidates)

        # 🧩 Caso nenhum nome tenha sido validado
        if not validated_names:
            logger.warning("Nenhum nome validado após checagem no banco de dados (possível timeout, max_len=0, ou nomes inválidos).")
            result = {
                "names": [],
                "unit_info": {"apartment": None, "block": None}
            }
            logger.info(f"Extração completa: {result}")
            return result

        # --- 7. Preenche dados faltantes de unidade ---
        if len(validated_names) == 1:
            single_name = next(iter(validated_names))
            unit_info = fill_missing_unit_info(single_name, names_with_units[single_name])
        else:
            for name in validated_names:
                names_with_units[name] = fill_missing_unit_info(name, names_with_units[name])

        # --- 8. Resultado final ---
        result = {"names": list(validated_names)}

        if len(validated_names) > 1:
            result["names_with_units"] = names_with_units
        else:
            single_name = next(iter(validated_names))
            result["unit_info"] = fill_missing_unit_info(single_name, unit_info)

        logger.info(f"Extração completa: {result}")
        return result

    except Exception as e:
        # --- Captura e loga qualquer erro inesperado ---
        logger.exception(f"Erro inesperado durante a execução do main(): {e}")
        # Retorna um resultado padrão de erro
        return {
            "names": [],
            "unit_info": {"apartment": None, "block": None},
            "error": str(e)
        }
