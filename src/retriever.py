from src.vector_store import load_vector_store


def get_retriever(username, k=3, search_type="mmr"):
    """Returns a retriever scoped to this user's private documents."""
    vector_store = load_vector_store(username)

    if search_type == "mmr":
        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k, "fetch_k": k * 4, "lambda_mult": 0.5}
        )
    else:
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )

    return retriever


def get_relevant_chunks(query, username, k=3, search_type="mmr", filename_filter=None):
    """Given a question, returns relevant chunks from this user's documents only."""
    vector_store = load_vector_store(username)

    search_kwargs = {"k": k}
    if filename_filter:
        search_kwargs["filter"] = {"source": filename_filter}
    if search_type == "mmr":
        search_kwargs["fetch_k"] = k * 4
        search_kwargs["lambda_mult"] = 0.5

    retriever = vector_store.as_retriever(
        search_type=search_type,
        search_kwargs=search_kwargs
    )

    return retriever.invoke(query)