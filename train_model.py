import random, spacy
from spacy.training.example import Example
from spacy.util import minibatch, compounding

# --- 1️⃣ Dados de treinamento ---
TRAIN_DATA = [
    (
        "Ruan Rodrigues Da Silva Rua Jonas da Fonseca, 250, 1 Condominio marrom apt 404",
        [("Ruan Rodrigues Da Silva", "DESTINATARIO"),
         ("Rua Jonas da Fonseca, 250, 1 Condominio marrom apt 404", "ENDERECO")]
    ),
    (
        "João Dias Rua João Negrão, 1251 Bloco, apartamento 112 80002-900 Curitiba/PR",
        [("João Dias", "DESTINATARIO"),
         ("Rua João Negrão, 1251 Bloco, apartamento 112 80002-900 Curitiba/PR", "ENDERECO")]
    )
]

# --- 2️⃣ Criar modelo vazio e adicionar NER ---
nlp = spacy.blank("pt")
ner = nlp.add_pipe("ner")
ner.add_label("DESTINATARIO")
ner.add_label("ENDERECO")

# --- 3️⃣ Treinamento ---
nlp.initialize()
for i in range(30):
    print(f"🔁 Iteração {i+1}/30")
    random.shuffle(TRAIN_DATA)
    batches = minibatch(TRAIN_DATA, size=compounding(1.0, 4.0, 1.5))
    for batch in batches:
        examples = []
        for text, entidades in batch:
            text_norm = text.replace("\n", " ").strip()
            doc = nlp.make_doc(text_norm)
            spans = []
            for ent_text, label in entidades:
                ent_text_norm = ent_text.replace("\n", " ").strip()
                start = text_norm.find(ent_text_norm)
                end = start + len(ent_text_norm)
                span = doc.char_span(start, end, label=label, alignment_mode="contract")
                if span:
                    spans.append((span.start_char, span.end_char, label))
            example = Example.from_dict(doc, {"entities": spans})
            examples.append(example)
        nlp.update(examples, drop=0.2)

# --- 4️⃣ Salvar modelo ---
modelo_path = "modelo_etiqueta"
nlp.to_disk(modelo_path)
print(f"✅ Modelo salvo em '{modelo_path}'")

# --- 5️⃣ Testar modelo com exemplo realista ---
nlp_test = spacy.load(modelo_path)
exemplo_teste = "João Dias Rua João Negrão, 1251 Bloco, apartamento 112 80002-900 Curitiba/PR"
doc = nlp_test(exemplo_teste)
for ent in doc.ents:
    print(ent.label_, ent.text)
