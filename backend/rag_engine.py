"""
Sanctuary 3.0 — RAG Engine
Real vector search using ChromaDB + sentence-transformers.
Supports HyDE (Hypothetical Document Embeddings) for clinical grounding.
"""

import logging
import chromadb
from chromadb.utils import embedding_functions

from config import Config
from cache_utils import SemanticCache

logger = logging.getLogger(__name__)

_collection = None
_ef = None
# Semantic in-memory cache for RAG retrievals (process-local)
_rag_cache = SemanticCache(capacity=Config.CACHE_SIZE_RAG, threshold=0.88)

# Clinical CBT protocols for grounding the LLM.
CLINICAL_PROTOCOLS = [
    # Anxiety-related distortions
    "CBT Protocol for Catastrophizing: The patient is imagining the worst-case scenario. "
    "Socratic reframe: What is the actual evidence for this outcome? What is the most likely outcome? "
    "What would you tell a friend in this situation?",

    "CBT Protocol for Fortune Telling: The patient is predicting negative outcomes without evidence. "
    "Socratic reframe: Have your predictions been accurate in the past? "
    "What are some alternative outcomes that are equally or more likely?",

    # Depression-related distortions
    "CBT Protocol for Overgeneralization: The patient uses 'always' or 'never' language. "
    "Socratic reframe: Is this truly a permanent pattern, or is it a single event? "
    "Can you recall a time when this was not the case?",

    "CBT Protocol for All-or-Nothing Thinking: The patient sees things in black and white. "
    "Socratic reframe: Is there a middle ground? What would 'good enough' look like?",

    "CBT Protocol for Labeling: The patient is assigning a global negative label to themselves. "
    "Socratic reframe: Is this label fair to your entire self? "
    "Does one event define who you are as a person?",

    # Self-blame distortions
    "CBT Protocol for Personalization: The patient blames themselves for things outside their control. "
    "Socratic reframe: What factors were actually within your control? "
    "What other people or circumstances contributed to this outcome?",

    "CBT Protocol for Emotional Reasoning: The patient believes something is true because they feel it. "
    "Socratic reframe: Just because you feel guilty, does that mean you are guilty? "
    "What would the evidence say if you looked at it objectively?",

    # Crisis intervention
    "Crisis Intervention Protocol: If the user expresses thoughts of self-harm, suicide, or harming others, "
    "immediately and compassionately provide emergency resources. "
    "Say: 'I hear you, and your safety matters most right now. Please reach out to the 988 Suicide & Crisis Lifeline "
    "(call or text 988) or go to your nearest emergency room.' "
    "Do NOT attempt therapy. Prioritize immediate safety.",

    # General therapeutic framing
    "Sanctuary System Prompt: You are a Socratic CBT reasoning engine. Your role is to: "
    "1) Validate the user's emotions. 2) Identify the specific cognitive distortion. "
    "3) Ask a gentle, non-judgmental Socratic question to help the user examine the thought. "
    "Never diagnose, prescribe medication, or replace professional therapy.",

    # Enhanced CBT Techniques
    "CBT Technique: Cognitive Rehearsal. The patient visualizes themselves successfully handling a difficult situation. "
    "Socratic reframe: What specific steps would you take in that situation? What strengths can you rely on?",
    
    "CBT Technique: Downward Arrow. Used to uncover underlying core beliefs. "
    "Socratic reframe: If that thought were true, what would it mean to you? Why would that be so bad?",

    "CBT Technique: Behavioral Activation. For depression, focusing on activities that provide mastery or pleasure. "
    "Socratic reframe: What is one small activity you used to enjoy that you could try for 5 minutes today?",

    "CBT Protocol for Disqualifying the Positive: The patient ignores positive experiences by insisting they don't count. "
    "Socratic reframe: Why do you feel this positive event doesn't count? If a friend did this, would you say it didn't count for them too?",
]


import pandas as pd
from pathlib import Path

def get_embedding_function():
    global _ef
    if _ef is None:
        _ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=Config.EMBEDDING_MODEL,
            device="cpu",
        )
    return _ef

def get_collection():
    """Lazy-initialize the ChromaDB collection."""
    global _collection
    if _collection is not None:
        return _collection

    logger.info("Initializing ChromaDB at %s ...", Config.CHROMA_DB_PATH)
    ef = get_embedding_function()
    client = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)
    _collection = client.get_or_create_collection(
        name="clinical_protocols",
        embedding_function=ef,
    )

    # Seed the database if it's empty
    if _collection.count() == 0:
        logger.info("Seeding clinical protocols into ChromaDB...")
        _collection.add(
            documents=CLINICAL_PROTOCOLS,
            ids=[f"protocol_{i}" for i in range(len(CLINICAL_PROTOCOLS))],
        )
        
        csv_path = Path(Config.KAGGLE_DATASET_PATH)
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                kaggle_docs = []
                for _, row in df.iterrows():
                    doc = (
                        f"Clinical Reference: Patient with {row.get('Diagnosis', 'Unknown Condition')}. "
                        f"Severity: {row.get('Symptom Severity (1-10)', 'N/A')}/10. "
                        f"Recommended Therapy: {row.get('Therapy Type', 'N/A')}. "
                        f"Medication: {row.get('Medication', 'N/A')}."
                    )
                    kaggle_docs.append(doc)
                _collection.add(
                    documents=kaggle_docs,
                    ids=[f"kaggle_{i}" for i in range(len(kaggle_docs))],
                )
            except: pass

    return _collection


_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        # Use a lightweight cross-encoder for reranking
        logger.info("Loading Cross-Encoder Reranker...")
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu")
    return _reranker

def retrieve_context(query: str, k: int = 2, hypothetical_query: str | None = None) -> str:
    """
    Retrieve clinical context using multi-stage refinement and Cross-Encoder reranking.
    """
    cache_key = (query, k, hypothetical_query)
    
    ef = get_embedding_function()
    try:
        search_text = hypothetical_query if hypothetical_query else query
        query_embedding = ef([search_text])[0]
    except Exception as e:
        logger.error("Failed to generate embedding: %s", e)
        query_embedding = None

    if query_embedding is not None:
        cached = _rag_cache.get(query_embedding)
        if cached is not None:
            return cached

    try:
        collection = get_collection()
        # Retrieve more candidates for reranking
        n_candidates = 10
        if query_embedding is not None:
            results = collection.query(query_embeddings=[query_embedding], n_results=n_candidates)
        else:
            results = collection.query(query_texts=[search_text], n_results=n_candidates)
            
        if results and results["documents"] and results["documents"][0]:
            docs = results["documents"][0]
            
            # Stage 2: Reranking with Cross-Encoder
            try:
                reranker = get_reranker()
                # Score each document against the original query
                pairs = [[query, doc] for doc in docs]
                scores = reranker.predict(pairs)
                
                # Sort docs by score
                scored_docs = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
                reranked_docs = [doc for doc, score in scored_docs]
                
                # Prioritize crisis docs if query is sensitive
                crisis_docs = [d for d in reranked_docs if "Crisis" in d]
                other_docs = [d for d in reranked_docs if "Crisis" not in d]
                refined_docs = (crisis_docs + other_docs)[:k]
            except Exception as re_err:
                logger.warning("Reranking failed, falling back to vector similarity: %s", re_err)
                refined_docs = docs[:k]
            
            out = "\n".join(refined_docs)
            if query_embedding is not None:
                _rag_cache.set(cache_key, query_embedding, out)
            return out
    except Exception as e:
        logger.error("RAG retrieval failed: %s", e)

    return ""
