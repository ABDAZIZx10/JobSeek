from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-en-v1.5"
# MODEL_NAME = "all-MiniLM-L6-v2"
model = None


def get_model():
    global model

    if model is None:
        print("loading embedding model into memory this may take some while")
        model = SentenceTransformer(MODEL_NAME)
        print("embedding model loaded")

    return model
