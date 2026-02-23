from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()  # <-- uvicorn looks for THIS

llm = ChatOpenAI(temperature=0.3, model="gpt-4o")  # fixed model name

class Query(BaseModel):
    question: str

@app.get("/")
def root():
    return {"status": "Agent is running!"}

@app.post("/ask")
def ask(query: Query):
    template = '''
        You are a helpful assistant who always replies cheerfully and with emojis 😄🎉
        Question: {question}
        Answer: 
    '''
    prompt = PromptTemplate(input_variables=["question"], template=template)
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"question": query.question})
    return {"answer": result}