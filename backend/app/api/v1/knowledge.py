"""Knowledge base endpoints — search and ingest."""
from fastapi import APIRouter, Depends
from app.api.schemas.requests import KnowledgeSearchRequest, KnowledgeIngestRequest
from app.api.schemas.responses import KnowledgeSearchResponse
from app.infrastructure.vector.chromadb_adapter import get_vector_store
from app.config.settings import get_settings

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])
settings = get_settings()


@router.post("/search", response_model=KnowledgeSearchResponse, summary="Semantic search across Oracle knowledge base")
async def search_knowledge(body: KnowledgeSearchRequest):
    vector_store = await get_vector_store()
    results = await vector_store.search_all_collections(
        query=body.query,
        module_filter=body.module,
        n_results_per_collection=body.n_results,
    )
    return KnowledgeSearchResponse(query=body.query, results=[{"content": r} for r in results], count=len(results))


@router.post("/ingest", summary="Ingest documents into knowledge base")
async def ingest_knowledge(body: KnowledgeIngestRequest):
    vector_store = await get_vector_store()
    collection_map = {
        "oracle_docs": settings.CHROMADB_COLLECTION_ORACLE_DOCS,
        "rca_history": settings.CHROMADB_COLLECTION_RCA_HISTORY,
        "sql_patterns": settings.CHROMADB_COLLECTION_SQL_PATTERNS,
        "config_guides": settings.CHROMADB_COLLECTION_CONFIG_GUIDES,
    }
    collection_name = collection_map.get(body.collection, settings.CHROMADB_COLLECTION_ORACLE_DOCS)
    metadatas = [{"module": body.module or "general", "source": body.source or "manual", "title": t} for t in (body.titles or [""] * len(body.documents))]
    count = await vector_store.ingest(collection_name=collection_name, documents=body.documents, metadatas=metadatas)
    return {"ingested": count, "collection": collection_name}
