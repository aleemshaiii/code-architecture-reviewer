import os
import json
import faiss
import numpy as np
from typing import List, Dict, Any

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "rules_catalog.json")

class MemoryVectorStore:
    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents: List[Dict[str, Any]] = []
        self._load_and_index_rules()

    def _pseudo_embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().replace("_", " ").replace(":", " ").replace("-", " ").split()
        if not words:
            return vec

        for word in words:
            idx = abs(hash(word)) % self.dimension
            vec[idx] += 1.0

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def _load_and_index_rules(self):
        rules = []
        if os.path.exists(CATALOG_PATH):
            with open(CATALOG_PATH, "r", encoding="utf-8-sig") as f:
                rules = json.load(f)

        if not rules:
            return

        vectors = []
        for rule in rules:
            searchable_text = f"{rule.get('title', '')} {rule.get('content', '')} {' '.join(rule.get('tags', []))}"
            vec = self._pseudo_embed(searchable_text)
            vectors.append(vec)
            self.documents.append(rule)

        matrix = np.array(vectors, dtype=np.float32)
        self.index.add(matrix)
        print(f"[FAISS] Successfully indexed {self.index.ntotal} architecture & security rules.")

    def search_similar(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        if self.index.ntotal == 0:
            return []

        query_vec = np.array([self._pseudo_embed(query)], dtype=np.float32)
        distances, indices = self.index.search(query_vec, min(top_k, self.index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.documents):
                doc_copy = dict(self.documents[idx])
                doc_copy["distance"] = float(dist)
                results.append(doc_copy)
        return results

vector_store = MemoryVectorStore()
