"""المرحلة 2: Embeddings + قاعدة Chroma (تخزين والبحث)"""
import chromadb
from sentence_transformers import SentenceTransformer

DB_DIR = "chroma_db"
COLLECTION = "docs"
# نموذج يدعم العربية والإنجليزية
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def get_collection():
    client = chromadb.PersistentClient(path=DB_DIR)
    return client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def add_chunks(docs, metas, ids):
    """يحول المقاطع لمتجهات ويحفظها في Chroma"""
    if not docs:
        return 0
    embeddings = get_model().encode(docs, normalize_embeddings=True).tolist()
    get_collection().upsert(ids=ids, documents=docs, embeddings=embeddings, metadatas=metas)
    return len(docs)


def search_chunks(query, k=4, source=None):
    """يرجع أقرب المقاطع للسؤال مع درجة التشابه"""
    col = get_collection()
    if col.count() == 0:
        return []
    q = get_model().encode([query], normalize_embeddings=True).tolist()
    kwargs = {"where": {"source": source}} if source else {}
    res = col.query(query_embeddings=q, n_results=k, **kwargs)
    return [
        {"text": d, "source": m["source"], "page": m["page"], "score": 1 - dist}
        for d, m, dist in zip(res["documents"][0],
                              res["metadatas"][0],
                              res["distances"][0])
    ]
