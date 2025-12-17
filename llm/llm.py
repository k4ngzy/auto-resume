import os

from dotenv import load_dotenv
from langchain.messages import HumanMessage
from langchain_openai import ChatOpenAI

load_dotenv()


API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "")


def create_llm():
    return ChatOpenAI(
        model_name="qwen3-max",
        api_key=API_KEY,
        base_url=BASE_URL,
        temperature=0.7,
    )


if __name__ == "__main__":
    llm = create_llm()
    response = llm.invoke([HumanMessage(content="你是什么模型?")])
    print(response.content)
