from src.db.queries import search_person_like, get_max_name_length, get_all_person_names, get_residents_by_apartment, get_residents_by_block, get_residents_by_unit, get_unit_info_by_name
from src.utils.utils import fuzzy_compare
from src.utils.normalize import normalize_name
from src.utils.logger import get_logger

logger = get_logger(__name__)

def validate_recipient_name_candidates(candidates: set):
    """
    Validação de candidatos extraídos pelo NER:
    - Testa nome completo via LIKE
    - Em caso de falha, tenta combinações parciais (janelas de 2+ tokens)
    - Fallback com fuzzy global, retornando top-3 por score >=70
    - Retorna tupla (set de nomes validados, dict de nomes com unidade)
    """
    validated_names = set()
    names_with_units = {}  # novo: armazena unidade por nome
    if not candidates:
        logger.info("Nenhum candidato recebido para validação.")
        return validated_names, names_with_units

    max_name_len = get_max_name_length()
    max_results_limit = 50
    all_names = None

    def safe_unpack_match(t):
        if not t:
            return None, 0
        if len(t) >= 2:
            return t[0], float(t[1])
        return t[0], 0.0

    def handle_fuzzy_with_near_matches(results, name):
        if not results:
            return set()
        scores = [safe_unpack_match(r)[1] for r in results]
        max_score = max(scores) if scores else 0
        near_matches = {normalize_name(safe_unpack_match(r)[0]) for r in results if safe_unpack_match(r)[1] == max_score}
        logger.debug(f"Near matches para '{name}' (score {max_score}): {near_matches}")
        return near_matches

    def generate_name_windows(tokens: list[str], min_size: int = 2) -> list[str]:
        windows = []
        for size in range(min_size, len(tokens)+1):
            for i in range(len(tokens)-size+1):
                windows.append(" ".join(tokens[i:i+size]))
        return windows

    for ner_name in candidates:
        logger.debug(f"Validando candidato: '{ner_name}'")
        if len(ner_name) > max_name_len:
            logger.info(f"Candidato '{ner_name}' descartado por ultrapassar max_name_len ({max_name_len})")
            continue

        # --- 1) LIKE completo ---
        results = search_person_like(ner_name)
        if len(results) == 1:
            normalized_name = normalize_name(results[0])
            validated_names.add(normalized_name)
            unit = get_unit_info_by_name(normalized_name)
            if unit:
                names_with_units[normalized_name] = unit
            logger.info(f"Nome '{ner_name}' validado via LIKE único: {results[0]}")
            continue

        elif len(results) > 1 and len(results) <= max_results_limit:
            matches = fuzzy_compare(candidates=results, name=ner_name)
            strong = set()
            if matches:
                for tup in matches:
                    m, s = safe_unpack_match(tup)
                    if s >= 70:
                        strong.add(normalize_name(m))
            if strong:
                for n in strong:
                    validated_names.add(n)
                    unit = get_unit_info_by_name(n)
                    if unit:
                        names_with_units[n] = unit
                logger.info(f"Nomes fortes de '{ner_name}' via fuzzy (>=70): {strong}")
                continue
            if matches:
                near = handle_fuzzy_with_near_matches(matches, ner_name)
                for n in near:
                    validated_names.add(n)
                    unit = get_unit_info_by_name(n)
                    if unit:
                        names_with_units[n] = unit
                logger.info(f"Nomes próximos de '{ner_name}' via fuzzy fallback: {near}")
                continue
            validated_names.update({normalize_name(r) for r in results})
            logger.info(f"Nomes múltiplos de '{ner_name}' sem necessidade de fuzzy: {results}")
            continue

        # --- 2) Janelas de tokens ---
        tokens = ner_name.split()
        found = False
        if len(tokens) > 1:
            windows = generate_name_windows(tokens, min_size=2)
            for combo in windows:
                res = search_person_like(combo)
                if not res or len(res) > max_results_limit:
                    continue
                matches = fuzzy_compare(candidates=res, name=ner_name)
                if matches:
                    strong = set()
                    for tup in matches:
                        m, s = safe_unpack_match(tup)
                        if s >= 70:
                            strong.add(normalize_name(m))
                    if strong:
                        for n in strong:
                            validated_names.add(n)
                            unit = get_unit_info_by_name(n)
                            if unit:
                                names_with_units[n] = unit
                        logger.info(f"'{ner_name}' validado via combinação '{combo}' e fuzzy forte: {strong}")
                        found = True
                        break
                    near = handle_fuzzy_with_near_matches(matches, ner_name)
                    if near:
                        for n in near:
                            validated_names.add(n)
                            unit = get_unit_info_by_name(n)
                            if unit:
                                names_with_units[n] = unit
                        logger.info(f"'{ner_name}' validado via combinação '{combo}' e fuzzy próximo: {near}")
                        found = True
                        break
            if found:
                continue

        # --- 3) Fallback fuzzy global ---
        if all_names is None:
            all_names = get_all_person_names()
        matches = fuzzy_compare(candidates=all_names, name=ner_name)
        if matches:
            strong_candidates = [(m, s) for m, s, *_ in matches if s >= 70]
            if len(strong_candidates) > 1:
                strong_candidates = sorted(strong_candidates, key=lambda x: x[1], reverse=True)[:3]
            for m, s in strong_candidates:
                normalized_name = normalize_name(m)
                validated_names.add(normalized_name)
                unit = get_unit_info_by_name(normalized_name)
                if unit:
                    names_with_units[normalized_name] = unit
                    logger.info(f"Nome '{normalized_name}' encontrado com unidade: {unit}")
                else:
                    logger.info(f"Nome '{normalized_name}' encontrado sem unidade associada.")
        else:
            logger.warning(f"Nenhum match encontrado para '{ner_name}' no fallback global.")

    logger.debug(f"Validação concluída. Nomes validados: {validated_names}")
    return validated_names, names_with_units

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

def validate_recipient_name_by_apartment(apartment: str, name_candidates: set) -> set:
    """
    Valida candidatos de nome usando apenas o número do apartamento (sem bloco).
    Faz fuzzy match entre os candidatos e todos os moradores de qualquer bloco com o mesmo número de unidade.
    """
    validated_names = set()
    if not apartment:
        logger.warning("Nenhum número de apartamento informado para validação.")
        return validated_names

    logger.info(f"Buscando moradores de todos os blocos no apartamento {apartment}")
    residents = get_residents_by_apartment(apartment)

    if not residents:
        logger.info(f"Nenhum morador encontrado para apartamento {apartment}.")
        return validated_names

    logger.debug(f"Moradores encontrados (por apartamento): {residents}")

    # --- Fuzzy matching ---
    for name in name_candidates:
        matches = fuzzy_compare(candidates=residents, name=name)
        if not matches:
            continue

        strong = {normalize_name(match) for match, score, _ in matches if score >= 70}
        if strong:
            validated_names.update(strong)
            logger.info(f"Nome '{name}' validado via fuzzy forte (>=70): {strong}")
        else:
            max_score = max(score for _, score, _ in matches)
            near = {normalize_name(match) for match, score, _ in matches if score == max_score}
            validated_names.update(near)
            logger.info(f"Nome '{name}' validado via fuzzy fallback (score {max_score}): {near}")

    logger.info(f"Validação por apartamento concluída. Resultados: {validated_names}")
    return validated_names


def validate_recipient_name_by_block(block: str, name_candidates: set) -> set:
    """
    Valida candidatos de nome usando apenas o bloco (sem número de apartamento).
    Faz fuzzy match entre os candidatos e todos os moradores daquele bloco.
    """
    validated_names = set()
    if not block:
        logger.warning("Nenhum bloco informado para validação.")
        return validated_names

    logger.info(f"Buscando moradores do bloco {block}")
    residents = get_residents_by_block(block)

    if not residents:
        logger.info(f"Nenhum morador encontrado para bloco {block}.")
        return validated_names

    logger.debug(f"Moradores encontrados (por bloco): {residents}")

    # --- Fuzzy matching ---
    for name in name_candidates:
        matches = fuzzy_compare(candidates=residents, name=name)
        if not matches:
            continue

        strong = {normalize_name(match) for match, score, _ in matches if score >= 70}
        if strong:
            validated_names.update(strong)
            logger.info(f"Nome '{name}' validado via fuzzy forte (>=70): {strong}")
        else:
            max_score = max(score for _, score, _ in matches)
            near = {normalize_name(match) for match, score, _ in matches if score == max_score}
            validated_names.update(near)
            logger.info(f"Nome '{name}' validado via fuzzy fallback (score {max_score}): {near}")

    logger.info(f"Validação por bloco concluída. Resultados: {validated_names}")
    return validated_names

def fill_missing_unit_info(name_or_candidates, unit_info: dict) -> dict:
    """
    Preenche unidade completa (apartment + block) baseado no(s) nome(s) do(s) candidato(s).
    name_or_candidates: str ou set[str]
    unit_info: dict parcial de unidade
    """
    if isinstance(name_or_candidates, str):
        name_candidates = {name_or_candidates}
    else:
        name_candidates = name_or_candidates

    apartment = unit_info.get("apartment")
    block = unit_info.get("block")

    # --- Decide a validação ---
    if apartment and block:
        validated_names = validate_recipient_name_by_unit(unit_info, name_candidates)
    elif apartment:
        validated_names = validate_recipient_name_by_apartment(apartment, name_candidates)
    elif block:
        validated_names = validate_recipient_name_by_block(block, name_candidates)
    else:
        # Nenhuma info de unidade → valida só pelo nome
        validated_names, _ = validate_recipient_name_candidates(name_candidates)
        logger.debug("Nenhum dado de unidade presente — validação feita apenas por nome.")

    if not validated_names:
        logger.info("Nenhum nome validado para preencher dados de unidade.")
        return unit_info

    # --- Consulta o banco pelo melhor candidato ---
    best_name = max(validated_names, key=len)
    full_unit = get_unit_info_by_name(best_name)
    if full_unit:
        if not apartment and full_unit.get("apartment"):
            unit_info["apartment"] = full_unit["apartment"]
            logger.info(f"Campo 'apartment' preenchido com '{full_unit['apartment']}' baseado no nome '{best_name}'")
        if not block and full_unit.get("block"):
            unit_info["block"] = full_unit["block"]
            logger.info(f"Campo 'block' preenchido com '{full_unit['block']}' baseado no nome '{best_name}'")
    else:
        logger.warning(f"Nenhum dado de unidade encontrado no banco para '{best_name}'.")

    return unit_info
