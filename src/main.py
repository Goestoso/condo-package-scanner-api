"""
Módulo principal que centralizará a lógica do programa
"""

from src.extractor import Extractor

def main():
    extractor = Extractor("Ana5.jpg")
    extractor.extract_text()
    
    extractor.extract_recipient_name()

    extractor.extract_recipient_address()
