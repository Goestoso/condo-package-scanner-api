from PIL import Image
import pytesseract
import spacy
import re

# --- Abrir imagem ---
img = Image.open("assets/correios.jpg")

# --- Extrair texto em português ---
texto = pytesseract.image_to_string(img, lang="por")

print("TESSERACT BRUTO:")
print(texto)
print("\n" + "-"*50 + "\n")

# --- Limpeza básica do texto ---
linhas = [l.strip() for l in texto.splitlines() if l.strip() != ""]

# Remover linhas irrelevantes típicas de etiquetas
linhas = [
    l for l in linhas 
    if not re.search(r'NF:|Pedido:|Shopee|XPRESS|DANFE|www|CORREIOS', l, re.IGNORECASE)
]

# Normalizar espaços e remover caracteres estranhos
texto = re.sub(r'\s+', ' ', texto).strip()

# Remover códigos, números longos, URLs, palavras irrelevantes
texto_limpo = " ".join([
    l for l in texto.splitlines() if not re.search(
        r'NF:|Pedido:|Shopee|XPRESS|DANFE|www|CORREIOS|\d{8,}|BR\d{10,}', 
        l, re.IGNORECASE
    )
])


# --- Carregar modelo SpaCy treinado ---
nlp = spacy.load("modelo_etiqueta")
doc = nlp(texto_limpo)

# --- Mostrar entidades reconhecidas ---
destinatario = []
endereco = []

linhas = [l.strip() for l in texto.splitlines() if l.strip() != ""]
for linha in linhas:
    doc = nlp(linha)
    for ent in doc.ents:
        if ent.label_ == "DESTINATARIO":
            destinatario.append(ent.text)
        elif ent.label_ == "ENDERECO":
            endereco.append(ent.text)


print("SPAcy NER RESULTADO:")
print("DESTINATARIO:", destinatario)
print("ENDERECO:", endereco)
