import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# ─────────────────────────────
# ChromaDB Setup
# ─────────────────────────────
CHROMA_DIR = "models/vector_store"
os.makedirs(CHROMA_DIR, exist_ok=True)

# Embedding function — sentence transformers
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# ChromaDB client
client = chromadb.PersistentClient(path=CHROMA_DIR)

# Collection banao
collection = client.get_or_create_collection(
    name="floatchat_knowledge",
    embedding_function=embedding_fn
)

# ─────────────────────────────
# Knowledge Base — Ocean Facts
# ─────────────────────────────
OCEAN_KNOWLEDGE = [
    {
        "id": "arabian_sea_1",
        "text": "Arabian Sea is located in the northwest Indian Ocean. It is bounded by India to the east, Pakistan and Iran to the north, and the Arabian Peninsula to the west. Latitude range: 8-26°N, Longitude range: 55-78°E.",
        "metadata": {"region": "arabian_sea", "type": "geography"}
    },
    {
        "id": "arabian_sea_2",
        "text": "Arabian Sea temperature ranges from 24°C to 30°C in summer months (April-September) and 20°C to 26°C in winter months (October-March). Surface temperatures are highest near the coast of India.",
        "metadata": {"region": "arabian_sea", "type": "temperature"}
    },
    {
        "id": "arabian_sea_3",
        "text": "Arabian Sea salinity ranges from 35 to 37 PSU. It is one of the saltiest seas in the Indian Ocean due to high evaporation rates and low freshwater input.",
        "metadata": {"region": "arabian_sea", "type": "salinity"}
    },
    {
        "id": "bay_of_bengal_1",
        "text": "Bay of Bengal is the northeastern part of the Indian Ocean. It is bounded by India to the west, Bangladesh to the north, and Myanmar to the east. Latitude range: 5-22°N, Longitude range: 80-100°E.",
        "metadata": {"region": "bay_of_bengal", "type": "geography"}
    },
    {
        "id": "bay_of_bengal_2",
        "text": "Bay of Bengal temperature ranges from 26°C to 30°C throughout the year. It receives large amounts of freshwater from major rivers like Ganges, Brahmaputra, and Irrawaddy.",
        "metadata": {"region": "bay_of_bengal", "type": "temperature"}
    },
    {
        "id": "bay_of_bengal_3",
        "text": "Bay of Bengal salinity is lower than Arabian Sea, ranging from 30 to 35 PSU due to large freshwater input from rivers. Near equator salinity is around 34 PSU.",
        "metadata": {"region": "bay_of_bengal", "type": "salinity"}
    },
    {
        "id": "indian_ocean_1",
        "text": "Indian Ocean is the third largest ocean in the world. The Argo float program monitors temperature, salinity, and pressure in Indian Ocean. Our database covers latitude 0-26°N and longitude 55-101°E.",
        "metadata": {"region": "indian_ocean", "type": "general"}
    },
    {
        "id": "argo_floats_1",
        "text": "Argo floats are autonomous underwater robots that measure ocean temperature, salinity, and pressure. They dive to 2000 meters depth and surface every 10 days to transmit data via satellite.",
        "metadata": {"region": "all", "type": "argo_info"}
    },
    {
        "id": "argo_floats_2",
        "text": "FloatChat database contains data from 265 unique Argo floats in the Indian Ocean region. Data spans from 2021 to 2026 with over 3 million oceanographic measurements.",
        "metadata": {"region": "indian_ocean", "type": "database_info"}
    },
    {
        "id": "temperature_depth_1",
        "text": "Ocean temperature decreases with depth. Surface temperature is warmest (24-30°C), thermocline layer at 100-1000m shows rapid decrease, and deep ocean below 1000m is cold (2-5°C).",
        "metadata": {"region": "all", "type": "oceanography"}
    },
    {
        "id": "salinity_1",
        "text": "Ocean salinity is measured in PSU (Practical Salinity Units). Normal ocean salinity is 34-36 PSU. Arabian Sea is saltier (35-37 PSU) than Bay of Bengal (30-35 PSU).",
        "metadata": {"region": "all", "type": "salinity"}
    },
    {
        "id": "monsoon_1",
        "text": "Indian Ocean is strongly influenced by monsoon seasons. Southwest monsoon (June-September) brings heavy rainfall. Northeast monsoon (October-January) is drier. Monsoons affect temperature and salinity patterns.",
        "metadata": {"region": "indian_ocean", "type": "climate"}
    },
    {
        "id": "incois_1",
        "text": "INCOIS (Indian National Centre for Ocean Information Services) is under Ministry of Earth Sciences, Government of India. It monitors Indian Ocean using Argo floats deployed by Indian Argo program.",
        "metadata": {"region": "indian_ocean", "type": "organization"}
    },
    {
        "id": "depth_pressure_1",
        "text": "Ocean depth is measured in dbar (decibars) of pressure. 1 dbar is approximately equal to 1 meter of ocean depth. Argo floats measure pressure from surface (0 dbar) to 2000 dbar depth.",
        "metadata": {"region": "all", "type": "oceanography"}
    },
    {
        "id": "bgc_1",
        "text": "BGC (Bio-Geo-Chemical) Argo floats measure additional parameters like dissolved oxygen (DOXY), chlorophyll (CHLA), pH, nitrate, and backscatter in addition to temperature and salinity.",
        "metadata": {"region": "all", "type": "bgc"}
    }
]

# ─────────────────────────────
# Knowledge Base Load Karo
# ─────────────────────────────
def load_knowledge_base():
    """Load ocean knowledge into ChromaDB"""

    # Already loaded hai?
    existing = collection.count()
    if existing > 0:
        print(f"Knowledge base already loaded: {existing} documents")
        return

    print("Loading knowledge base into ChromaDB...")

    texts    = [doc["text"]     for doc in OCEAN_KNOWLEDGE]
    ids      = [doc["id"]       for doc in OCEAN_KNOWLEDGE]
    metadata = [doc["metadata"] for doc in OCEAN_KNOWLEDGE]

    collection.add(
        documents=texts,
        ids=ids,
        metadatas=metadata
    )

    print(f"Loaded {len(texts)} documents into ChromaDB!")

# ─────────────────────────────
# Query — Relevant Context Lo
# ─────────────────────────────
def get_relevant_context(query: str, n_results: int = 3) -> str:
    """
    User query ke liye relevant context return karo
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )

    if not results or not results['documents']:
        return ""

    context_parts = results['documents'][0]
    context       = "\n".join(context_parts)

    return context

# ─────────────────────────────
# RAG Enhanced SQL Generator
# ─────────────────────────────
def ask_with_rag(user_query: str) -> dict:
    """
    RAG pipeline:
    1. Relevant context lo ChromaDB se
    2. Context + Query → Better SQL
    3. DB se data lo
    4. Answer generate karo
    """
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.sql_generator import generate_sql, run_query, explain_result

    # Step 1: Context lo
    context = get_relevant_context(user_query)
    print(f"\nContext found: {len(context)} chars")

    # Step 2: Context ke saath enhanced query
    enhanced_query = user_query
    if context:
        enhanced_query = f"""
Context about Indian Ocean:
{context}

User Question: {user_query}
"""

    # Step 3: SQL generate karo
    result = generate_sql(enhanced_query)
    sql    = result['sql']
    print(f"SQL: {sql}")

    # Step 4: DB se data lo
    db_result = run_query(sql)
    print(f"DB Result: {db_result[:2]}")

    # Step 5: Answer generate karo
    answer = explain_result(user_query, sql, db_result)
    print(f"Answer: {answer}")

    return {
        "query"  : user_query,
        "context": context,
        "sql"    : sql,
        "data"   : db_result,
        "answer" : answer
    }

# ─────────────────────────────
# Initialize
# ─────────────────────────────
def initialize_rag():
    """RAG system initialize karo"""
    print("Initializing RAG system...")
    load_knowledge_base()
    print("RAG system ready!")

# ─────────────────────────────
# Test
# ─────────────────────────────
if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    initialize_rag()

    test_queries = [
        "What is the temperature in Arabian Sea?",
        "How salty is the Bay of Bengal?",
        "How many Argo floats are in Indian Ocean?",
    ]

    for query in test_queries:
        print(f"\n{'='*50}")
        result = ask_with_rag(query)
        print(f"Answer: {result['answer']}")