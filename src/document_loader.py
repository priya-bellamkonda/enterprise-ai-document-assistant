import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader


def load_documents(folder_path="data/uploaded_documents"):
    """
    Reads all PDF and Word documents from the given folder
    and returns them as a list of LangChain 'document' objects.
    """
    documents = []

    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return documents

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        try:
            if filename.lower().endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                loaded = loader.load()
                documents.extend(loaded)
                print(f"Loaded PDF: {filename} ({len(loaded)} pages)")

            elif filename.lower().endswith(".docx"):
                loader = Docx2txtLoader(file_path)
                loaded = loader.load()
                documents.extend(loaded)
                print(f"Loaded Word doc: {filename}")

            else:
                print(f"Skipped unsupported file: {filename}")

        except Exception as e:
            print(f"Error loading {filename}: {e}")

    print(f"\nTotal documents loaded: {len(documents)}")
    return documents


# Lets us test this file directly without running the whole app
if __name__ == "__main__":
    docs = load_documents()
    if docs:
        print("\n--- Preview of first document ---")
        print(docs[0].page_content[:500])  # show first 500 characters