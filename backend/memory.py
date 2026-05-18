"""
Sanctuary 3.0 — Long-Term Memory Engine
Handles session summarization and vectorized retrieval of past clinical themes.
"""

import logging
import chromadb
import json
from datetime import datetime
from config import Config
from rag_engine import get_embedding_function

logger = logging.getLogger(__name__)

_summary_collection = None

def get_summary_collection():
    """Lazy-initialize the ChromaDB collection for session summaries."""
    global _summary_collection
    if _summary_collection is not None:
        return _summary_collection

    logger.info("Initializing Summary Memory at %s ...", Config.CHROMA_DB_PATH)
    ef = get_embedding_function()
    from chromadb.config import Settings
    client = chromadb.PersistentClient(
        path=Config.CHROMA_DB_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    _summary_collection = client.get_or_create_collection(
        name="session_summaries",
        embedding_function=ef,
    )
    return _summary_collection

def summarize_session(session_id: str, messages: list) -> str:
    """
    Generate a clinical summary of a session using the LLM.
    """
    from llm_engine import get_inference_orchestrator
    
    if not messages:
        return ""

    # Format history for summarization
    history_text = ""
    for m in messages:
        role = "User" if m.get("role") == "user" else "Sanctuary"
        history_text += f"{role}: {m.get('text')}\n"

    summary_prompt = (
        "You are a clinical supervisor reviewing a CBT session. Summarize the following session "
        "into a single concise paragraph. Focus on: \n"
        "1. Core themes (e.g., relationship anxiety, work stress).\n"
        "2. Recurring cognitive distortions identified.\n"
        "3. Any progress made or key insights the user reached.\n\n"
        f"SESSION TRANSCRIPT:\n{history_text}\n\n"
        "CONCISE CLINICAL SUMMARY:"
    )

    messages = [{"role": "system", "content": "You are a clinical supervisor. Be objective and concise."},
                {"role": "user", "content": summary_prompt}]
    
    orchestrator = get_inference_orchestrator()
    summary = orchestrator.generate(messages, max_tokens=250)
    
    # Store in ChromaDB
    collection = get_summary_collection()
    collection.add(
        documents=[summary],
        metadatas=[{"session_id": session_id, "timestamp": datetime.now().isoformat()}],
        ids=[f"summary_{session_id}_{int(datetime.now().timestamp())}"]
    )
    
    logger.info("Session %s summarized and stored in long-term memory.", session_id)
    return summary

def retrieve_past_memories(query: str, k: int = 2) -> str:
    """
    Retrieve relevant past session summaries to provide long-term continuity.
    """
    try:
        collection = get_summary_collection()
        if collection.count() == 0:
            return ""
            
        results = collection.query(query_texts=[query], n_results=k)
        if results and results["documents"] and results["documents"][0]:
            memories = results["documents"][0]
            return "\n".join([f"- Past Context: {m}" for m in memories])
    except Exception as e:
        logger.error("Memory retrieval failed: %s", e)
        
    return ""
