from io import BytesIO
from PIL import Image
import pytesseract
from pathlib import Path
from src.utils.logger import get_logger

class CondoPackageLabel:

    def __init__(self, image, in_memory=False):
        self.logger = get_logger(self.__class__.__name__)
        if in_memory:
            self.__image_path = None
            self.__image = Image.open(BytesIO(image))
            self.logger.info("Sticker criado a partir de imagem em memória.")
        else:
            self.__image_path = image
            self.__image = Image.open(self.image_path)
            self.logger.info(f"Sticker criado para a imagem: {self.__image_path}")


    @property
    def text(self):
        return self.__text

    @property
    def image_path(self):
        return self.__image_path

    def extract_text(self):
        try:
            self.logger.debug("Iniciando OCR na imagem...")
            self.__text = pytesseract.image_to_string(self.__image, lang="por")
            self.logger.info(f"OCR concluído ({len(self.__text)} caracteres)")
        except Exception as e:
            self.logger.error(f"Erro no OCR: {e}")
            raise

    def __str__(self):
        return f"OCR:\n\n{self.text}\n"
