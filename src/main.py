"""
Ponto de entrada principal do aplicativo quando executado como script
ou chamado pela API.

Este módulo delega a extração ao controller.
"""

from src.controller.extract_controller import extract_package_info_controller
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main(image_input):
    logger.info("Iniciando App...")
    
    result = extract_package_info_controller(image_input)
    
    logger.info("Encerrando App...")
    return result
