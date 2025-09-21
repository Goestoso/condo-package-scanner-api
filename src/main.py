"""
Módulo principal que centralizará a lógica do programa
"""

from src.extractor import Extractor

def main():
    extractor = Extractor("Loggi.jpg")
    extractor.extract_text()
    
    print(extractor)

    extractor.extract_recipient_name()

    extractor.extract_recipient_address()

    print(extractor)