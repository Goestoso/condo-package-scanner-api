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
    Controller com fallback completo:
        unit → apartment → block → global
    """
    try:
        # --------------------------
        # 1. Instância extractor
        # --------------------------
        if isinstance(image_input, (str, Path)):
            extractor = Extractor(image_input)
        elif isinstance(image_input, (bytes, BytesIO)):
            extractor = Extractor(image_input, in_memory=True)
        else:
            raise TypeError("Parâmetro inválido: esperado caminho (str) ou bytes de imagem.")

        # --------------------------
        # 2. OCR
        # --------------------------
        extractor.extract_text()

        # --------------------------
        # 3. Candidatos a nomes
        # --------------------------
        extractor.extract_recipient_name()
        raw_candidates = extractor.candidates_name
        sanitized_candidates = {sanitize_name_cand(c) for c in raw_candidates if sanitize_name_cand(c)}

        if not sanitized_candidates:
            return format_success_result(
                names_with_units={}, 
                reason="Nenhum candidato de nome válido encontrado na etiqueta."
            )

        # --------------------------
        # 4. Endereço e unidade
        # --------------------------
        extractor.extract_recipient_address()
        unit_info = extractor.extract_apartment_and_block() or {"apartment": None, "block": None}
        unit_info["block"] = normalize_block(unit_info.get("block"))

        apartment = unit_info.get("apartment")
        block = unit_info.get("block")

        validated_names = set()
        names_with_units = {}

        logger.info(f"Iniciando validação: ap={apartment}, block={block}, candidates={sanitized_candidates}")

        # =====================================================================
        # FALLBACK COMPLETO
        # =====================================================================

        # 1) unit = apartment + block
        if apartment and block:
            logger.info("Tentando validação por unidade (ap + bloco)...")
            validated_names = validate_recipient_name_by_unit(unit_info, sanitized_candidates)
            if validated_names:
                names_with_units = {name: dict(unit_info) for name in validated_names}
                logger.info("Validação bem-sucedida via unidade.")
            else:
                logger.info("Falha na validação por unidade. Indo para fallback de apartamento...")

        # 2) fallback: apartment somente
        if not validated_names and apartment:
            logger.info("Fallback: tentando validação apenas por apartamento...")
            validated_names = validate_recipient_name_by_apartment(apartment, sanitized_candidates)
            if validated_names:
                names_with_units = {name: {"apartment": apartment, "block": None} for name in validated_names}
                logger.info("Validação bem-sucedida via apartamento.")
            else:
                logger.info("Falha no fallback por apartamento. Indo para fallback de bloco...")

        # 3) fallback: block somente
        if not validated_names and block:
            logger.info("Fallback: tentando validação apenas por bloco...")
            validated_names = validate_recipient_name_by_block(block, sanitized_candidates)
            if validated_names:
                names_with_units = {name: {"apartment": None, "block": block} for name in validated_names}
                logger.info("Validação bem-sucedida via bloco.")
            else:
                logger.info("Falha no fallback por bloco. Indo para validação global...")

        # 4) fallback global por nome (LIKE + fuzzy)
        if not validated_names:
            logger.info("Último fallback: validação global por nome (LIKE + fuzzy)...")
            validated_names, names_with_units = validate_recipient_name_candidates(sanitized_candidates)

        # --------------------------
        # 5. Nenhum nome validado?
        # --------------------------
        if not validated_names:
            return format_success_result(
                names_with_units={},
                reason="Nenhum nome validado no banco de dados."
            )

        # --------------------------
        # 6. Completar unidade ausente
        # --------------------------
        for name in validated_names:
            names_with_units[name] = fill_missing_unit_info(name, names_with_units.get(name, {}))

        # --------------------------
        # 7. Retorno final
        # --------------------------
        return format_success_result(
            names_with_units=names_with_units,
            reason=(
                "Candidatos com nomes similares validados no banco de dados"
                if len(validated_names) > 1
                else "Candidato único validado no banco de dados"
            )
        )

    except Exception as e:
        logger.exception(f"Erro inesperado durante a extração: {e}")
        return format_error_result(e)
