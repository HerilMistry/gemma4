"""
Sanctuary 3.0 — RAG Engine
Real vector search using ChromaDB + sentence-transformers.
Replaces the broken mock FAISS that returned random vectors.

The embedding model (all-MiniLM-L6-v2) downloads once on first run (~80MB),
then works fully offline from the local cache.
"""

import logging
import chromadb
from chromadb.utils import embedding_functions

from config import Config

logger = logging.getLogger(__name__)

_collection = None

# Clinical CBT protocols for grounding the LLM.
# These are the verified therapeutic frameworks the model is allowed to reference.
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
]


import pandas as pd
from pathlib import Path

def get_collection():
    """Lazy-initialize the ChromaDB collection with clinical protocols and Kaggle dataset."""
    global _collection
    if _collection is not None:
        return _collection

    logger.info("Initializing ChromaDB at %s ...", Config.CHROMA_DB_PATH)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=Config.EMBEDDING_MODEL,
        device="cpu",
    )
    client = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)
    _collection = client.get_or_create_collection(
        name="clinical_protocols",
        embedding_function=ef,
    )

    # Seed the database if it's empty
    if _collection.count() == 0:
        logger.info("Seeding clinical protocols into ChromaDB...")
        
        # 1. Add hardcoded protocols
        _collection.add(
            documents=CLINICAL_PROTOCOLS,
            ids=[f"protocol_{i}" for i in range(len(CLINICAL_PROTOCOLS))],
        )
        
        # 2. Add Kaggle dataset if available
        csv_path = Path(Config.KAGGLE_DATASET_PATH)
        if csv_path.exists():
            logger.info("Indexing Kaggle dataset from %s ...", csv_path)
            try:
                df = pd.read_csv(csv_path)
                # Map CSV rows to descriptive strings for RAG
                # Expected columns: Diagnosis, Symptom Severity (1-10), Therapy Type, Medication
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
                logger.info("Successfully indexed %d Kaggle records.", len(kaggle_docs))
            except Exception as e:
                logger.error("Failed to index Kaggle dataset: %s", e)
        else:
            logger.warning("Kaggle dataset not found at %s. Skipping Kaggle indexing.", csv_path)

        logger.info("Seeding complete.")

    return _collection



def retrieve_context(query: str, k: int = 2) -> str:
    """
    Retrieve the top-k most relevant clinical protocols for a given user query.

    Args:
        query: The user's journal text.
        k: Number of protocols to retrieve.

    Returns:
        A newline-joined string of the most relevant protocols.
    """
    try:
        collection = get_collection()
        results = collection.query(query_texts=[query], n_results=k)
        if results and results["documents"] and results["documents"][0]:
            return "\n".join(results["documents"][0])
    except Exception as e:
        logger.error("RAG retrieval failed: %s", e)

    return ""
