from src.sticker import Sticker

if __name__ == '__main__':
    data = Sticker("shopee.jpg")
    data.extract_recipient()
    print(data)
    print(f"Nome: {data.recipient_name}")
    print(f"Residência: {data.recipient_residence}")