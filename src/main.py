"""
Módulo principal que centraliza a lógica do programa:
1. Extrai texto da imagem via OCR
2. Identifica candidatos a nomes (NER)
3. Sanitiza e valida nomes usando banco + fuzzy
4. Extrai endereço (pode ter lógica similar)
"""

from src.extractor import Extractor
from src.utils.validators import validate_recipient_name_candidates, validate_recipient_name_by_unit
from src.utils.normalize import normalize_block
from src.utils.sanitize import sanitize_name_cand
from src.utils.logger import get_logger

logger = get_logger(__name__)

def main(image_path: str):
    logger.info(f"Iniciando extração da imagem: {image_path}")

    # --- 1. Instancia o extractor ---
    extractor = Extractor(image_path)

    # --- 2. OCR ---
    extractor.extract_text()
    logger.info("OCR concluído.")
    
    # --- 3. Extrai candidatos a nomes (NER) ---
    extractor.extract_recipient_name()
    candidates = extractor.candidates_name

    # --- 3.1. Sanitiza os candidatos ---
    sanitized_candidates = {sanitize_name_cand(c) for c in candidates if sanitize_name_cand(c)}
    logger.debug(f"Candidatos a nomes sanitizados: {sanitized_candidates}")

    # --- 4. Extrai endereço ---
    extractor.extract_recipient_address()
    address = extractor.candidates_address
    logger.debug(f"Endereço extraído: {address}")

    # --- 5. Extrai ap/bloco ---
    unit_info = extractor.extract_apartment_and_block()
    unit_info['block'] = normalize_block(unit_info['block'])

    # --- 6. Escolhe o tipo de validação ---
    if unit_info:
        logger.info(f"Validando por unidade: {unit_info}")
        validated_names = validate_recipient_name_by_unit(unit_info, sanitized_candidates)
    else:
        logger.info("Nenhuma unidade identificada. Usando validação apenas por nome.")
        validated_names = validate_recipient_name_candidates(sanitized_candidates)

    # --- 7. Resultado final ---
    result = {
        "names": list(validated_names),
        "unit_info": unit_info
    }

    logger.info(f"Extração completa: {result}")
    return result
