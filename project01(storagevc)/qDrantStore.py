from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from numpy import ndarray
import uuid 

def storeVector(client: QdrantClient, job, vector:ndarray):
    client.upsert(
        collection_name=os.getenv("COLLECTION_NAME"),
        points=[
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector.tolist(),
                payload=job
            )
        ]
    )

def SearchVector(limit:int, client: QdrantClient, QueryVector:ndarray):
    result = client.query_points(
        collection_name=os.getenv("COLLECTION_NAME"),
        query=QueryVector,
        limit=limit,
        with_payload=True
    )
    return result
    

def connect():
    load_dotenv()
    print("connecting to the qDrant Database")
    client = QdrantClient(
        host=os.getenv("HOST"),
        port=os.getenv("PORT")
    )
    
    COLLECTION_NAME = os.getenv("COLLECTION_NAME")
    
    try:
        print("checking if collection already exists")
        exists = client.get_collection(COLLECTION_NAME)
    except Exception as E:
        print("Creating non existing collection")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )
    return client
