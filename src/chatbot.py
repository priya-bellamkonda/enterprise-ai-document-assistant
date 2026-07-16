from src.retriever import get_retriever
from src.llm import get_llm


def build_context(chunks):
    """Combines retrieved chunks into a single text block."""
    context = "\n\n".join([chunk.page_content for chunk in chunks])
    return context


def build_chat_history_text(chat_history):
    """Turns previous Q&A pairs into a simple text block."""
    if not chat_history:
        return "No previous conversation."

    history_text = ""
    for turn in chat_history:
        history_text += f"User: {turn['question']}\nAssistant: {turn['answer']}\n\n"
    return history_text


def ask_question(question, username, chat_history=None, k=3, filename_filter=None):
    """
    Given a question, the user's username, and optional chat history/filename filter:
    1. Finds the most relevant chunks from THIS USER's documents only
    2. Sends them + the question + chat history to the AI
    3. Returns a clear, grounded answer with source info
    """
    if chat_history is None:
        chat_history = []

    search_kwargs = {"k": k, "fetch_k": k * 4, "lambda_mult": 0.5}
    if filename_filter:
        search_kwargs["filter"] = {"source": filename_filter}

    from src.vector_store import load_vector_store
    vector_store = load_vector_store(username)
    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs
    )

    chunks = retriever.invoke(question)
    context = build_context(chunks)
    history_text = build_chat_history_text(chat_history)

    llm = get_llm()

    prompt = f"""You are an enterprise document assistant. Answer the question 
using ONLY the context provided below. If the answer is not in the context, 
say "I don't have enough information in the documents to answer that."

Use the previous conversation to understand follow-up questions.

Previous conversation:
{history_text}

Context from documents:
{context}

Current question: {question}

Answer:"""

    response = llm.invoke(prompt)

    sources_info = []
    for chunk in chunks:
        filename = chunk.metadata.get("source", "Unknown file")
        filename = filename.split("\\")[-1].split("/")[-1]
        page = chunk.metadata.get("page", "N/A")
        sources_info.append({
            "filename": filename,
            "page": page,
            "text": chunk.page_content
        })

    return {
        "answer": response.content,
        "sources": sources_info
    }
def summarize_document(username, filename=None):
    """Generates a summary of one document (or all documents if filename is None)."""
    return _run_document_task(
        username,
        filename,
        instruction="Write a clear, well-organized summary of the following document content in 4-6 sentences."
    )


def generate_key_points(username, filename=None):
    """Generates key bullet points from the document."""
    return _run_document_task(
        username,
        filename,
        instruction="Extract the 5-8 most important key points from the following document content. Format as a bullet list."
    )


def generate_faqs(username, filename=None):
    """Generates FAQs based on the document content."""
    return _run_document_task(
        username,
        filename,
        instruction="Based on the following document content, generate 5 likely frequently asked questions (FAQs) along with clear answers. Format as Q&A pairs."
    )


def extract_action_items(username, filename=None):
    """Extracts action items / tasks from the document."""
    return _run_document_task(
        username,
        filename,
        instruction="Extract all action items, tasks, or next steps mentioned in the following document content. Format as a numbered list. If none exist, say so clearly."
    )


def _run_document_task(username, filename, instruction):
    """
    Shared helper: pulls a broad sample of chunks from the document(s)
    and asks the AI to perform the given instruction on them.
    """
    from src.vector_store import load_vector_store

    vector_store = load_vector_store(username)

    search_kwargs = {"k": 15}  # pull more chunks than usual, since we want broad coverage
    if filename:
        search_kwargs["filter"] = {"source": filename}

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs
    )

    # Generic broad query just to pull relevant chunks across the document
    chunks = retriever.invoke("summary overview main content")
    context = build_context(chunks)

    llm = get_llm()

    prompt = f"""{instruction}

Document content:
{context}
"""

    response = llm.invoke(prompt)
    return response.content


if __name__ == "__main__":
    history = []

    