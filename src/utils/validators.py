from src.db.queries import search_person_like, get_max_name_length, get_all_person_names, get_residents_by_apartment, get_residents_by_block, get_residents_by_unit, get_unit_info_by_name
from src.utils.utils import fuzzy_compare
from src.utils.normalize import normalize_name
from src.utils.logger import get_logger

logger = get_logger(__name__)


def validate_recipient_name_candidates(candidates: set):
    """
    Valida nomes identificados pelo NER com múltiplas estratégias:
    1) LIKE do nome completo
    2) LIKE por tokens individuais
    3) Janelas de tokens (fallback)
    4) Fuzzy global (último recurso)
    Retorna:
        - set de nomes validados
        - dict nome->unidade
    """

    validated = set()
    names_with_units = {}

    if not candidates:
        logger.info("Nenhum candidato recebido para validação.")
        return validated, names_with_units

    max_name_len = get_max_name_length()
    max_results = 50
    all_names_cache = None  # lazy loading

    # -----------------------------------------------------
    # Helpers
    # -----------------------------------------------------

    def safe_score(entry):
        return (entry[0], float(entry[1])) if entry and len(entry) >= 2 else (None, 0.0)

    def select_by_fuzzy(results, target, threshold=70, limit=None):
        matches = fuzzy_compare(candidates=results, name=target)
        if not matches:
            logger.debug(f"Nenhum match fuzzy encontrado para '{target}'")
            return set()

        selected = [(normalize_name(n), s) for n, s in matches if s >= threshold]

        if selected:
            logger.info(f"'{target}' validado via fuzzy forte: {[n for n, _ in selected]}")
        else:
            # fallback — pega o(s) de maior score
            max_score = max(s for _, s in matches)
            selected = [(normalize_name(n), s) for n, s in matches if s == max_score]
            logger.info(f"'{target}' validado via fuzzy fallback (score {max_score})")

        selected.sort(key=lambda x: x[1], reverse=True)
        if limit:
            selected = selected[:limit]

        return {n for n, _ in selected}

    def select_by_fuzzy_global(all_names, target, global_threshold=55, limit=None):
        matches = fuzzy_compare(candidates=all_names, name=target)
        if not matches:
            logger.debug(f"Nenhum match fuzzy global encontrado para '{target}'")
            return set()

        matches.sort(key=lambda x: x[1], reverse=True)
        best_name, best_score = matches[0]

        if best_score < global_threshold:
            logger.debug(f"Melhor score com '{best_name}', porém score {best_score} < {global_threshold} (treshold do fuzzy global)")
            logger.info(
                f"'{target}' descartado por não atingir treshold do fuzzy global."
            )
            return set()

        selected = [(normalize_name(n), s) for n, s in matches if s >= global_threshold]

        if limit:
            selected = selected[:limit]

        logger.info(f"'{target}' validado via fuzzy global: {[n for n, _ in selected]}")

        return {n for n, _ in selected}

    def get_units_for(names: set):
        out = {}
        for n in names:
            unit = get_unit_info_by_name(n)
            if unit:
                out[n] = unit
        return out

    # -----------------------------------------------------
    # PROCESSAMENTO DE CADA NOME
    # -----------------------------------------------------

    for raw_name in candidates:
        ner_name = raw_name.strip()
        logger.debug(f"Validando candidato: '{ner_name}'")

        # descartar nomes absurdamente longos
        if len(ner_name) > max_name_len:
            logger.info(f"Candidato '{ner_name}' descartado por ultrapassar tamanho máximo.")
            continue

        tokens = [t for t in ner_name.split() if len(t) >= 2]
        all_like_results = set()

        # -------------------------------------------------
        # 1) LIKE pelo nome completo
        # -------------------------------------------------
        results = search_person_like(ner_name)

        if not results:
            logger.info(f"'{ner_name}' não retornou LIKE — tentando outras estratégias...")

        if len(results) == 1:
            normalized = normalize_name(results[0])
            validated.add(normalized)
            names_with_units.update(get_units_for({normalized}))
            logger.info(f"'{ner_name}' validado via LIKE único.")
            continue

        if 1 < len(results) <= max_results:
            strong = select_by_fuzzy(results, ner_name)
            if strong:
                validated.update(strong)
                names_with_units.update(get_units_for(strong))
                continue

            matches = fuzzy_compare(results, ner_name)
            if matches:
                max_score = max(safe_score(x)[1] for x in matches)
                near = {normalize_name(safe_score(x)[0]) for x in matches if safe_score(x)[1] == max_score}
                validated.update(near)
                names_with_units.update(get_units_for(near))
                logger.info(f"'{ner_name}' validado via melhor score do LIKE+fuzzy.")
                continue

            # nenhum fuzzy útil → valida todos mesmo assim
            normalized_all = {normalize_name(r) for r in results}
            validated.update(normalized_all)
            logger.info(f"'{ner_name}' validado via LIKE múltiplo sem fuzzy.")
            continue

        # -------------------------------------------------
        # 2) LIKE pelos tokens
        # -------------------------------------------------
        for tok in tokens:
            res = search_person_like(tok)
            if res and len(res) <= max_results:
                all_like_results.update(res)

        if all_like_results:
            strong = select_by_fuzzy(list(all_like_results), ner_name)
            if strong:
                validated.update(strong)
                names_with_units.update(get_units_for(strong))
                continue

        # -------------------------------------------------
        # 3) Janelas de tokens
        # -------------------------------------------------
        if len(tokens) >= 2:
            for i in range(len(tokens) - 1):
                window = f"{tokens[i]} {tokens[i+1]}"
                res = search_person_like(window)
                if res and len(res) <= max_results:
                    strong = select_by_fuzzy(res, ner_name)
                    if strong:
                        validated.update(strong)
                        names_with_units.update(get_units_for(strong))
                        break

            if ner_name in validated:
                continue

        # -------------------------------------------------
        # 4) Fuzzy global (lazy loading)
        # -------------------------------------------------
        if all_names_cache is None:
            all_names_cache = get_all_person_names()
            if not all_names_cache:
                logger.error("Falha ao carregar nomes para fuzzy global.")
                all_names_cache = []

        strong = select_by_fuzzy_global(all_names_cache, ner_name, global_threshold=55, limit=3)

        if strong:
            validated.update(strong)
            names_with_units.update(get_units_for(strong))
        else:
            logger.warning(f"Nenhum match encontrado para '{ner_name}' nem no fuzzy global.")

    logger.debug(f"Validação concluída. Nomes validados: {validated}")
    return validated, names_with_units



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

    # --- Busca moradores ---
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

    # --- Fuzzy matching ---
    for ner_name in name_candidates:
        matches = fuzzy_compare(residents, ner_name)
        if not matches:
            continue

        # nomes com score >= 70
        strong = {normalize_name(match) for match, score in matches if score >= 70}
        if strong:
            validated_names.update(strong)
            logger.info(f"Nome '{ner_name}' validado via fuzzy forte (>=70): {strong}")
        else:
            # fallback: nomes com score máximo
            max_score = max(score for _, score in matches)
            near = {normalize_name(match) for match, score in matches if score == max_score}
            validated_names.update(near)
            logger.info(f"Nome '{ner_name}' validado via fuzzy fallback (score {max_score}): {near}")

    logger.info(f"Validação por unidade concluída. Resultados: {validated_names} - {str(unit_info)}")
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

    for name in name_candidates:
        matches = fuzzy_compare(residents, name)
        if not matches:
            continue

        strong = {normalize_name(match) for match, score in matches if score >= 70}
        if strong:
            validated_names.update(strong)
            logger.info(f"Nome '{name}' validado via fuzzy forte (>=70): {strong}")
        else:
            max_score = max(score for _, score in matches)
            near = {normalize_name(match) for match, score in matches if score == max_score}
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

    for name in name_candidates:
        matches = fuzzy_compare(residents, name)
        if not matches:
            continue

        strong = {normalize_name(match) for match, score in matches if score >= 70}
        if strong:
            validated_names.update(strong)
            logger.info(f"Nome '{name}' validado via fuzzy forte (>=70): {strong}")
        else:
            max_score = max(score for _, score in matches)
            near = {normalize_name(match) for match, score in matches if score == max_score}
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
