"""
Módulo principal que centraliza a lógica do programa:
1. Extrai texto da imagem via OCR
2. Identifica candidatos a nomes (NER)
3. Sanitiza e valida nomes usando banco + fuzzy
4. Extrai endereço (pode ter lógica similar)
"""

from src.extractor import Extractor
from src.utils.validators import validate_recipient_name_candidates, validate_recipient_name_by_unit
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
    logger.info(f"Candidatos NER extraídos: {candidates}")

    # --- 4. Valida nomes extraídos ---
    validated_names = validate_recipient_name_candidates(candidates)
    extractor.validated_names = validated_names
    logger.info(f"Nomes validados: {validated_names}")

    # --- 5. Extrai endereço ---
    extractor.extract_recipient_address()
    address = extractor.recipient_address
    logger.info(f"Endereço extraído: {address}")

    # --- 6. Extrai ap/bloco ---
    unit_info = extractor.extract_apartment_and_block()

    # --- 7. Escolhe o tipo de validação ---
    if unit_info:
        logger.info(f"Validando por unidade: {unit_info}")
        validated_names = validate_recipient_name_by_unit(unit_info, extractor.candidates_name)
    else:
        logger.info("Nenhuma unidade identificada. Usando validação apenas por nome.")
        validated_names = validate_recipient_name_candidates(extractor.candidates_name)

    # --- 8. Resultado final ---
    result = {
        "names": list(validated_names),
        "unit_info": unit_info
    }

    logger.info(f"Extração completa: {result}")
    return result
