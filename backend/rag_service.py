from typing import List, Dict
from models import ReferenceMaterial

# Mock Vector DB Interface
class VectorDB:
    def __init__(self):
        self.store = {}
    
    def add_texts(self, texts: List[str], metadatas: List[Dict]):
        # In real app: embed texts -> upsert to Pinecone/Chroma
        for i, text in enumerate(texts):
            doc_id = metadatas[i]['id']
            self.store[doc_id] = {"text": text, "metadata": metadatas[i]}
    
    def similarity_search(self, query: str, top_k=3) -> List[Dict]:
        # In real app: embed query -> search
        # Returning dummy results for prototype
        results = []
        for doc_id, data in list(self.store.items())[:top_k]:
            results.append(data)
        return results

vector_db = VectorDB()

class RAGService:
    def ingest_reference_material(self, material: ReferenceMaterial):
        """
        Chunks and indexes reference material.
        """
        # 1. Chunking (Simple split for now)
        chunk_size = 500
        text = material.text_content
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        # 2. Metadata
        metadatas = [{"id": f"{material.id}_{i}", "source": material.filename} for i in range(len(chunks))]
        
        # 3. Embedding & Storage
        vector_db.add_texts(chunks, metadatas)
        print(f"Ingested {len(chunks)} chunks from {material.filename}")

    def retrieve_context(self, query: str, context_ids: List[str] = None) -> str:
        """
        Retrieves relevant context for a given query (student submission part).
        """
        results = vector_db.similarity_search(query)
        context_text = "\n\n".join([f"[Source: {r['metadata']['source']}]\n{r['text']}" for r in results])
        return context_text
