from models.jobfilters import JobFilters
from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchText,
    Range,
    TextIndexParams,
    TokenizerType,
    SparseVectorParams,
    SparseIndexParams,
    Prefetch,
    FusionQuery,
    Fusion

)
from numpy import ndarray
import uuid 

def storeVector(client: QdrantClient, job, vector:ndarray):
    client.upsert(
        collection_name=os.getenv("COLLECTION_NAME"),
        points=[
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=job
            )
        ]
    )


def build_qdrant_filter(filters: JobFilters):
    conditions = []

    if filters.location is not None:
        conditions.append(
            FieldCondition(
                key="job_filters.location",
                match=MatchText(text=filters.location)
            )
        )

    if filters.remote is not None:
        conditions.append(
            FieldCondition(
                key="job_filters.remote",
                match=MatchValue(value=filters.remote)
            )
        )

    if filters.seniority is not None:
        conditions.append(
            FieldCondition(
                key="job_filters.seniority",
                match=MatchText(text=filters.seniority)
            )
        )

    if filters.min_salary is not None:
        conditions.append(
            FieldCondition(
                key="job_filters.max_salary",
                range=Range(gte=filters.min_salary)
            )
        )

    if filters.max_salary is not None:
        conditions.append(
            FieldCondition(
                key="job_filters.min_salary",
                range=Range(lte=filters.max_salary)
            )
        )

    if filters.visa_sponsorship is not None:
        conditions.append(
            FieldCondition(
                key="job_filters.visa_sponsorship",
                match=MatchValue(value=filters.visa_sponsorship)
            )
        )

    if filters.clearance_required is not None:
        conditions.append(
            FieldCondition(
                key="job_filters.clearance_required",
                match=MatchValue(value=filters.clearance_required)
            )
        )

    if filters.max_age_days is not None:
        conditions.append(
            FieldCondition(
                key="job_filters.max_age_days",
                range=Range(lte=filters.max_age_days)
            )
        )

    if not conditions:
        return None
    return Filter(must=conditions)


def SearchVector(
    limit: int,
    client: QdrantClient,
    dense_vector: ndarray,
    sparse_vector,
    query_filter=None
):
    result = client.query_points(
        collection_name=os.getenv("COLLECTION_NAME"),

        prefetch=[
            Prefetch(
                query=dense_vector,
                using="dense",
                limit=20
            ),
            Prefetch(
                query=sparse_vector,
                using="sparse",
                limit=20
            )
        ],

        query=FusionQuery(
            fusion=Fusion.RRF
        ),

        limit=limit,
        with_payload=True,
        query_filter=query_filter
    )

    return result


    

def connect():
    load_dotenv()
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    os.environ["no_proxy"] = "127.0.0.1,localhost"
    client = QdrantClient(
        url="http://127.0.0.1:6333"
    )
    
    COLLECTION_NAME = os.getenv("COLLECTION_NAME")
    
    try:
        exists = client.get_collection(COLLECTION_NAME)
    except Exception:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
            "dense": VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(
                index=SparseIndexParams(on_disk=False)
            )
        }

        )
    
    # Ensure full-text indices exist for case-insensitive matching
    for field in ["job_filters.location", "job_filters.seniority"]:
        try:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field,
                field_schema=TextIndexParams(
                    type="text",
                    tokenizer=TokenizerType.WORD,
                    lowercase=True
                )
            )
        except Exception:
            pass

    return client
