import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import chromadb




def load_test_documents(folder_path):
    """Loads all PDF/Word docs from a folder for testing."""
    documents = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.lower().endswith(".pdf"):
            documents.extend(PyPDFLoader(file_path).load())
        elif filename.lower().endswith(".docx"):
            documents.extend(Docx2txtLoader(file_path).load())
    return documents


def test_chunk_size(documents, chunk_size, chunk_overlap=200):
    """Tests a specific chunk size and returns timing + chunk count."""
    start = time.time()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(documents)

    split_time = time.time() - start

    return {
        "chunk_size": chunk_size,
        "num_chunks": len(chunks),
        "split_time_seconds": round(split_time, 3)
    }


def test_retrieval_speed(chunks, embedding_model_name, test_queries):
    """
    Builds a temporary vector store with the given embedding model,
    then measures retrieval time for each test query.
    """
    chromadb.api.client.SharedSystemClient.clear_system_cache()

    embeddings = OpenAIEmbeddings(model=embedding_model_name)

    start_embed = time.time()
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=f"data/eval_temp_{embedding_model_name.replace('-', '_')}"
    )
    embed_time = time.time() - start_embed

    query_times = []
    for query in test_queries:
        start_query = time.time()
        results = vector_store.similarity_search(query, k=3)
        query_time = time.time() - start_query
        query_times.append({
            "query": query,
            "time_seconds": round(query_time, 3),
            "num_results": len(results)
        })

    avg_query_time = sum(q["time_seconds"] for q in query_times) / len(query_times)

    return {
        "embedding_model": embedding_model_name,
        "embedding_time_seconds": round(embed_time, 3),
        "avg_query_time_seconds": round(avg_query_time, 3),
        "query_details": query_times
    }


if __name__ == "__main__":
    print("=" * 60)
    print("EVALUATION: Document Assistant RAG Pipeline")
    print("=" * 60)

    print(f"\nLoading test documents from: {TEST_DOCUMENT_FOLDER}")
    documents = load_test_documents(TEST_DOCUMENT_FOLDER)
    print(f"Loaded {len(documents)} document page(s)\n")

    # --- Test 1: Chunk size comparison ---
    print("-" * 60)
    print("TEST 1: Chunk Size Comparison")
    print("-" * 60)

    chunk_sizes_to_test = [500, 1000, 1500]
    chunk_results = []

    for size in chunk_sizes_to_test:
        result = test_chunk_size(documents, size)
        chunk_results.append(result)
        print(f"Chunk size {size}: {result['num_chunks']} chunks, "
              f"split in {result['split_time_seconds']}s")

    # --- Test 2: Embedding model comparison ---
    print("\n" + "-" * 60)
    print("TEST 2: Embedding Model Comparison")
    print("-" * 60)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)

    embedding_models_to_test = ["text-embedding-3-small", "text-embedding-3-large"]
    embedding_results = []

    for model_name in embedding_models_to_test:
        print(f"\nTesting: {model_name}")
        result = test_retrieval_speed(chunks, model_name, TEST_QUERIES)
        embedding_results.append(result)
        print(f"  Embedding time: {result['embedding_time_seconds']}s")
        print(f"  Avg query time: {result['avg_query_time_seconds']}s")

    # --- Summary ---
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\nChunk Size Results:")
    for r in chunk_results:
        print(f"  {r['chunk_size']} chars -> {r['num_chunks']} chunks ({r['split_time_seconds']}s)")

    print("\nEmbedding Model Results:")
    for r in embedding_results:
        print(f"  {r['embedding_model']}: embed={r['embedding_time_seconds']}s, "
              f"avg_query={r['avg_query_time_seconds']}s")