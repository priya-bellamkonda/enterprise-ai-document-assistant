import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm():
    """
    Returns a GPT chat model that will generate answers
    based on the context we give it.
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini",  # cheap and good quality
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0  # 0 = focused, factual answers (not creative/random)
    )
    return llm


# Test this file directly
if __name__ == "__main__":
    llm = get_llm()

    response = llm.invoke("Say hello and confirm you're working.")
    print(response.content)