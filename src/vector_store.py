import os
import chromadb
from langchain_chroma import Chroma
from src.embeddings import get_embedding_model


def get_persist_directory(username):
    """Returns the database folder path specific to this user."""
    return f"data/users/{username}/chroma_db"


def create_vector_store(chunks, username):
    """
    Takes text chunks, converts them to embeddings, and stores them
    in this user's private ChromaDB folder.
    """
    chromadb.api.client.SharedSystemClient.clear_system_cache()

    embeddings = get_embedding_model()
    persist_directory = get_persist_directory(username)

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )

    print(f"Vector store created with {len(chunks)} chunks for user: {username}")
    return vector_store


def load_vector_store(username):
    """Loads this user's private vector store from disk."""
    chromadb.api.client.SharedSystemClient.clear_system_cache()

    embeddings = get_embedding_model()
    persist_directory = get_persist_directory(username)

    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )

    print(f"Vector store loaded for user: {username}")
    return vector_store