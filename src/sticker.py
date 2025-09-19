from PIL import Image
import pytesseract
from pathlib import Path

class Sticker:

    def __init__(self, image: str):
        base_dir = Path(__file__).parent
        self.__image_path = base_dir.parent / "assets" / image
        self.__text = ""  # atributo para guardar o text extraído do OCR

    @property
    def text(self):
        return self.__text

    @property
    def image_path(self):
        return self.__image_path
        
    def extract_text(self):
        img = Image.open(str(self.image_path))
        self.__text: str = str(pytesseract.image_to_string(img, lang="por"))

    
    def __str__(self):
        return (
            f"OCR:" +  f"\n\n{self.text}\n"
        )

