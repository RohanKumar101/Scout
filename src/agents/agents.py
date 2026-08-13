from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.tools.tools import web_search, scrape_url
from dotenv import load_dotenv
import os

load_dotenv()

#model initialization
# groq_api_key = os.getenv("GROQ_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

# llm = ChatGroq(
#     model = "llama-3.1-8b-instant",
#     temperature=0,
#     api_key=groq_api_key,
# )

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=google_api_key,
)


# agent 1
def build_search_agent():
    return create_agent(
        model = llm,
        tools = [web_search],
    )

# agent 2

def build_reader_agent():
    return create_agent(
        model = llm,
        tools = [scrape_url],
    )

#writer chain

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clean , structured and insightful reports."),
    ("human", """write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Verified Source URLs (include these exact links in Sources):
{sources}

Structure the report as:
- Introduction
- Key Findings(minimum 3 well-explained points)
- Conclusion
- Sources (list each URL from "Verified Source URLs" as a markdown bullet)

Be detailed , factual and profressional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()


#critic chain

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths::
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()
