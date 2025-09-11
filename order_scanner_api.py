from src.sticker import Sticker

if __name__ == '__main__':
    condominio_enderecos = [
        "Rua Jonas da Fonseca, 250, 1 Condominio marrom apt 404",
        "Rua Jonas da Fonseca, 250, Condomínio azul, apartamento 112"
    ]

    sticker = Sticker("Ana.jpg")

    print(Sticker.sanitize(sticker.text))

    sticker.extract_recipient_name()
    print(f"Nome detectado: {sticker.recipient_name}")