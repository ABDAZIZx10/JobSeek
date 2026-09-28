from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
MODEL_NAME = "BAAI/bge-small-en-v1.5"
# MODEL_NAME = "all-MiniLM-L6-v2"
model = None


def get_model():
    global model

    if model is None:
        model = SentenceTransformer(MODEL_NAME)

    return model
def get_sparse_model():
    sparse_model = SparseTextEmbedding(
    model_name="Qdrant/bm25"
    )
    return sparse_model


