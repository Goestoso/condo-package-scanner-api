from PIL import Image
import pytesseract
from pathlib import Path
from src.utils.logger import get_logger

class Sticker:

    def __init__(self, image: str):
        self.logger = get_logger(self.__class__.__name__)
        base_dir = Path(__file__).parent
        self.__image_path = base_dir.parent / "assets" / image
        self.__text = ""  # atributo para guardar o texto extraído do OCR
        self.logger.info(f"Sticker criado para a imagem: {self.__image_path}")

    @property
    def text(self):
        return self.__text

    @property
    def image_path(self):
        return self.__image_path

    def extract_text(self):
        """Executa OCR na imagem e armazena o texto."""
        try:
            self.logger.debug(f"Iniciando OCR na imagem: {self.image_path}")
            img = Image.open(str(self.image_path))
            self.__text = str(pytesseract.image_to_string(img, lang="por"))
            self.logger.info(f"OCR concluído. Texto extraído com {len(self.__text)} caracteres")
        except FileNotFoundError:
            self.logger.error(f"Arquivo não encontrado: {self.image_path}")
            raise
        except Exception as e:
            self.logger.error(f"Erro ao executar OCR: {e}")
            raise

    def __str__(self):
        return f"OCR:\n\n{self.text}\n"
