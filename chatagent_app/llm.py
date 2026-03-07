import os
from dotenv import load_dotenv

load_dotenv()

provider = os.getenv("LLM_PROVIDER", "groq").lower()

if provider == "groq":
    from langchain_groq import ChatGroq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")

    llm = ChatGroq(
        groq_api_key=api_key,
        model_name=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        temperature=0
    )

# elif provider == "openai":
#     from langchain_openai import ChatOpenAI

#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         raise ValueError("OPENAI_API_KEY not found in environment variables.")

#     llm = ChatOpenAI(
#         openai_api_key=api_key,
#         model_name=os.getenv("OPENAI_MODEL", "gpt-4o"),
#         temperature=0
#     )

# else:
#     raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")