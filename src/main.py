"""
Módulo principal que centralizará a lógica do programa
"""

from src.extractor import Extractor

def main():
    extractor = Extractor("ml_aba.jpg")
    extractor.extract_text()

    print(extractor)

    extractor.extract_recipient_name()

    print(extractor)

    extractor.extract_recipient_address()

    print(extractor)