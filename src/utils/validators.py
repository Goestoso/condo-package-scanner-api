from src.db.queries import search_person_like, get_max_name_length, get_all_person_names, get_residents_by_apartment, get_residents_by_block, get_residents_by_unit
from src.utils.utils import fuzzy_compare
from src.utils.normalize import normalize_name
from src.utils.logger import get_logger

logger = get_logger(__name__)

def validate_recipient_name_candidates(candidates: set):
    """
    Validação de candidatos extraídos pelo NER:
    1. Descarta candidatos maiores que o max_name_len
    2. Consulta LIKE por nome completo
    3. Se nada, tenta buscar por sobrenome(s)
    4. Fallback fuzzy só se absolutamente nenhum resultado
    5. Função interna para casos de fuzzy sem match >= 70
    """

    validated_names = set()
    if not candidates:
        logger.info("Nenhum candidato recebido para validação.")
        return validated_names

    max_name_len = get_max_name_length()
    all_names = None  # será carregado só se precisarmos do fallback fuzzy

    def handle_fuzzy_with_near_matches(results, name):
        """
        Caso nenhum match do fuzzy alcance o threshold, retorna os nomes com maior score.
        """
        if not results:
            logger.debug(f"Nenhum resultado de fuzzy para '{name}'")
            return set()
        max_score = max(score for _, score in results)
        near_matches = {normalize_name(match) for match, score in results if score == max_score}
        logger.debug(f"Near matches para '{name}' (score {max_score}): {near_matches}")
        return near_matches

    for name in candidates:
        logger.debug(f"Validando candidato: '{name}'")
        if len(name) > max_name_len:
            logger.info(f"Candidato '{name}' descartado por ultrapassar max_name_len ({max_name_len})")
            continue

        # 1. LIKE completo
        results = search_person_like(name)
        logger.debug(f"Resultados LIKE para '{name}': {results}")
        if len(results) == 1:
            validated_names.add(normalize_name(results[0]))
            logger.info(f"Nome '{name}' validado com sucesso via LIKE único: {results[0]}")
            continue
        elif len(results) > 1:
            # Se fuzzy ainda não der match, usar near matches
            matches = fuzzy_compare(candidates=results, name=name)
            if matches:
                strong_matches = {normalize_name(match) for match, score in matches if score >= 70}
                if strong_matches:
                    validated_names.update(strong_matches)
                    logger.info(f"Nomes fortes de '{name}' via fuzzy (>=70): {strong_matches}")
                else:
                    near = handle_fuzzy_with_near_matches(matches, name)
                    validated_names.update(near)
                    logger.info(f"Nomes próximos de '{name}' via fuzzy fallback: {near}")
            else:
                validated_names.update({normalize_name(r) for r in results})
                logger.info(f"Nomes múltiplos de '{name}' sem necessidade de fuzzy: {results}")
            continue

        # 2. Tenta por sobrenome(s)
        tokens = name.split()
        found = False
        for surname in reversed(tokens[1:]):
            results = search_person_like(surname)
            if results:
                validated_names.update({normalize_name(r) for r in results})
                logger.info(f"Nome '{name}' encontrado via sobrenome '{surname}': {results}")
                found = True
                break

        # 3. Fallback fuzzy completo
        if not found:
            if all_names is None:
                all_names = get_all_person_names()
            matches = fuzzy_compare(candidates=all_names, name=name)
            if matches:
                strong_matches = {normalize_name(match) for match, score in matches if score >= 70}
                if strong_matches:
                    validated_names.update(strong_matches)
                    logger.info(f"Nomes fortes de '{name}' via fallback fuzzy completo (>=70): {strong_matches}")
                else:
                    near = handle_fuzzy_with_near_matches(matches, name)
                    validated_names.update(near)
                    logger.info(f"Nomes próximos de '{name}' via fallback fuzzy completo: {near}")
            else:
                logger.info(f"Nenhum match encontrado para '{name}' mesmo após fallback completo.")

    logger.debug(f"Validação concluída. Nomes validados: {validated_names}")
    return validated_names

def validate_recipient_name_by_unit(unit_info: dict, name_candidates: set) -> set:
    """
    Valida candidatos de nome com base na unidade do endereço (apartamento/bloco).
    1. Usa os moradores da unidade como base.
    2. Aplica fuzzy matching com os candidatos NER.
    3. Retorna nomes com score >= 70 ou os mais próximos (fallback).
    """

    validated_names = set()
    apartment = unit_info.get("apartment")
    block = unit_info.get("block")

    if not (apartment or block):
        logger.warning("Nenhum dado de unidade informado para validação.")
        return validated_names

    # --- 1. Busca moradores conforme o que temos ---
    residents = set()
    if apartment and block:
        logger.info(f"Buscando moradores do apartamento {apartment}, bloco {block}")
        residents = get_residents_by_unit(apartment, block)
    elif apartment:
        logger.info(f"Buscando moradores de todos os blocos no apartamento {apartment}")
        residents = get_residents_by_apartment(apartment)
    elif block:
        logger.info(f"Buscando moradores do bloco {block}")
        residents = get_residents_by_block(block)

    if not residents:
        logger.info("Nenhum morador encontrado para a unidade especificada.")
        return validated_names

    logger.debug(f"Moradores encontrados: {residents}")

    # --- 2. Aplica fuzzy matching entre NER e nomes do banco ---
    all_matches = []
    for name in name_candidates:
        matches = fuzzy_compare(candidates=residents, name=name)
        if matches:
            all_matches.append((name, matches))

    if not all_matches:
        logger.info("Nenhum match fuzzy encontrado entre candidatos e moradores.")
        return validated_names

    # --- 3. Seleciona os melhores resultados ---
    for ner_name, matches in all_matches:
        # Ignorando o terceiro valor retornado pelo fuzzy_compare (_)
        strong = {normalize_name(match) for match, score, _ in matches if score >= 70}
        if strong:
            validated_names.update(strong)
            logger.info(f"Nome '{ner_name}' validado via fuzzy forte (>=70): {strong}")
        else:
            # fallback: usa os com score máximo
            max_score = max(score for _, score, _ in matches)
            near = {normalize_name(match) for match, score, _ in matches if score == max_score}
            validated_names.update(near)
            logger.info(f"Nome '{ner_name}' validado via fuzzy fallback (score {max_score}): {near}")

    logger.info(f"Validação por unidade concluída. Resultados: {validated_names}")
    return validated_names
