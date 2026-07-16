from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    """
    Splits loaded documents into smaller chunks.
    chunk_size: how many characters per chunk
    chunk_overlap: how much chunks overlap (so context isn't lost at the edges)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    chunks = splitter.split_documents(documents)
    print(f"Split {len(documents)} document(s) into {len(chunks)} chunks")

    return chunks


# Lets us test this file directly
if __name__ == "__main__":
    import sys
    import os

    # Add project root to path so we can import from src/
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from src.document_loader import load_documents

    docs = load_documents()
    chunks = split_documents(docs)

    if chunks:
        print("\n--- Preview of first chunk ---")
        print(chunks[0].page_content)
        print(f"\nChunk length: {len(chunks[0].page_content)} characters")