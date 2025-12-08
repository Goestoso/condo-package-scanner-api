import spacy
import cupy as cp

print("CuPy versão:", cp.__version__)
print("Número de GPUs detectadas:", cp.cuda.runtime.getDeviceCount())

# Testar spaCy
import spacy
spacy.require_gpu()
print("GPU disponível para spaCy!")
