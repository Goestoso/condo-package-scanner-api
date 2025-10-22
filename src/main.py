"""
Módulo principal que centraliza a lógica do programa:
1. Extrai texto da imagem via OCR
2. Identifica candidatos a nomes (NER)
3. Sanitiza e valida nomes usando banco + fuzzy
4. Extrai endereço (pode ter lógica similar)
"""

from src.extractor import Extractor
from src.utils.validators import validate_recipient_name_candidates, validate_recipient_name_by_unit, validate_recipient_name_by_apartment, validate_recipient_name_by_block, fill_missing_unit_info
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
    unit_info = extractor.extract_apartment_and_block() or {"apartment": None, "block": None}
    unit_info['block'] = normalize_block(unit_info['block'])

    # --- 6. Valida nomes ---
    if unit_info.get('apartment') and unit_info.get('block'):
        validated_names = validate_recipient_name_by_unit(unit_info, sanitized_candidates)
        names_with_units = {name: unit_info for name in validated_names}
    elif unit_info.get('apartment'):
        validated_names = validate_recipient_name_by_apartment(unit_info['apartment'], sanitized_candidates)
        names_with_units = {name: {"apartment": unit_info['apartment'], "block": None} for name in validated_names}
    elif unit_info.get('block'):
        validated_names = validate_recipient_name_by_block(unit_info['block'], sanitized_candidates)
        names_with_units = {name: {"apartment": None, "block": unit_info['block']} for name in validated_names}
    else:
        # nova função retorna: (nomes validados, dict de nome -> unidade)
        validated_names, names_with_units = validate_recipient_name_candidates(sanitized_candidates)

    # --- 7. Preenche dados faltantes de unidade ---
    if len(validated_names) == 1:
        # apenas um candidato, preenche unit_info diretamente
        single_name = next(iter(validated_names))
        unit_info = fill_missing_unit_info(single_name, names_with_units[single_name])
    else:
        # vários candidatos, garante que cada um tenha unidade
        for name in validated_names:
            names_with_units[name] = fill_missing_unit_info(name, names_with_units[name])

    # --- 8. Resultado final ---
    result = {
        "names": list(validated_names)
    }

    if len(validated_names) > 1:
        # múltiplos nomes → names_with_units
        for name in validated_names:
            names_with_units[name] = fill_missing_unit_info(name, names_with_units.get(name, {}))
        result["names_with_units"] = names_with_units
    else:
        # 1 nome → unit_info
        single_name = next(iter(validated_names))
        unit_info = fill_missing_unit_info(single_name, unit_info)
        result["unit_info"] = unit_info

    logger.info(f"Extração completa: {result}")
    return result
