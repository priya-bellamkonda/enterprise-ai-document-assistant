import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

# Load the API key from .env file
load_dotenv()


def get_embedding_model():
    """
    Returns an OpenAI embeddings model.
    This turns text into lists of numbers representing meaning.
    """
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",  # cheap and good quality
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    return embeddings


# Test this file directly
if __name__ == "__main__":
    embeddings = get_embedding_model()

    # Try embedding a simple test sentence
    test_text = "This is a test sentence for embeddings."
    result = embeddings.embed_query(test_text)

    print(f"Embedding generated successfully!")
    print(f"Vector length: {len(result)}")
    print(f"First 5 numbers: {result[:5]}")