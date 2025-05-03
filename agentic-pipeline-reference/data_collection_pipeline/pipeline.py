from IPython import get_ipython
from IPython.display import display
import os
from langchain.tools import tool
from typing import List, Dict, Union
from tavily import TavilyClient
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from typing import TypedDict, List
import functools
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from typing import Annotated
from pydantic import BaseModel
import operator
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import BaseMessage
from newspaper import Article

# SECURITY NOTE: Never hardcode API keys in your code. Always use environment variables.
os.environ["OPENAI_API_KEY"] = "KEY"
os.environ["TAVILY_API_KEY"] = "KEY"

# Tavily Search Tool
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
@tool
def search_links(query: str) -> List[Dict]:
    """Use Tavily to search for high-signal articles or blog posts related to engineering growth, performance, and promotions."""
    print("🔍 Searching for links...")
    results = tavily_client.search(query=query, max_results=2)  # Reduced from 5 to 2
    print(f"📥 Found {len(results.get('results', []))} results")
    curated_links = [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "content": r.get("content", ""),
            "source": r.get("source", "unknown")
        }
        for r in results.get("results", [])
    ]
    print(f"✨ Curated {len(curated_links)} links")
    return curated_links

@tool
def extract_and_clean_content(url: str) -> dict:
    """Extracts and cleans the main article content from a URL. Returns cleaned text and metadata."""
    print(f"📄 Extracting and cleaning content from {url}")
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        # Clean the text
        text = article.text.strip()
        cleaned_text = text[:3000] if text else ""  # cap to 3K chars
        
        result = {
            "url": url,
            "text": cleaned_text,
            "title": article.title.strip(),
            "authors": article.authors,
            "publish_date": str(article.publish_date) if article.publish_date else None,
        }
        print(f"✅ Successfully extracted and cleaned content from {url}")
        return result
    except Exception as e:
        print(f"❌ Failed to extract content from {url}: {str(e)}")
        return {"url": url, "error": f"Failed to extract content: {str(e)}"}

# Agent Wrapper
def create_agent(llm, tools: List, system_prompt: str):
    """Create a function-calling agent using your standardized class pattern."""
    system_prompt += (
        "\nWork autonomously according to your specialty, using the tools available to you."
        " Do not ask for clarification."
        " Your other team members (and other teams) will collaborate with you with their own specialties."
        " You are chosen for a reason!"
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("messages"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

# Agent Node Wrapper
def agent_node(state, agent, name):
    print(f"\n🔄 Running {name}...")
    print(f"📦 Current state keys: {list(state.keys())}")
    result = agent.invoke(state)
    print(f"📝 {name} result: {result}")
    # Preserve the existing state and add the new message
    updated_state = {**state, "messages": [HumanMessage(content=result["output"], name=name)]}
    print(f"📦 Updated state keys: {list(updated_state.keys())}")
    return updated_state

# Supervisor Wrapper
def create_team_supervisor(llm, system_prompt, members):
    """Create a function-calling router LLM for supervising agents."""
    options = ["FINISH"] + members
    function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [{"enum": options}],
                },
            },
            "required": ["next"],
        },
    }
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next?"
                " Or should we FINISH? Select one of: {options}"
                "\n\n"
                "IMPORTANT: You must follow this exact sequence:"
                "1. Start with DataCurator"
                "2. Then ContentExtractor"
                "3. Then CleanContentAgent"
                "4. Finally FINISH"
                "\n\n"
                "Do not skip any steps. Each agent must be called in sequence."
            ),
        ]
    ).partial(options=str(options), team_members=", ".join(members))
    
    def log_supervisor_decision(state):
        print(f"\n🧠 Supervisor making decision...")
        print(f"📦 Current state keys: {list(state.keys())}")
        result = (
            prompt
            | llm.bind_functions(functions=[function_def], function_call="route")
            | JsonOutputFunctionsParser()
        ).invoke(state)
        print(f"🎯 Supervisor decided to route to: {result['next']}")
        return result
    
    return log_supervisor_decision

# Define the state object
class CurationAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    query: str
    curated_links: List[dict]
    extracted_content: List[dict]
    cleaned_content: List[dict]  # <-- NEW
    team_members: List[str]
    next: str

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4-turbo-preview", api_key=os.environ.get("OPENAI_API_KEY", ""))

# Create the agent
data_curator_agent = create_agent(
    llm=llm,
    tools=[search_links],
    system_prompt="""You are a research assistant who curates high-quality links and resources
about engineering growth, performance rubrics, and workplace culture. Use your tools to search and return
a diverse, non-duplicate list of curated URLs related to the user's query."""
)

content_extractor_agent = create_agent(
    llm=llm,
    tools=[extract_and_clean_content],
    system_prompt="""You are a content extractor who receives curated URLs and uses tools to extract and clean the full article text and metadata.
Only return results from successful extractions. Do not fabricate or guess."""
)

# Wrap it in a node
curator_node = functools.partial(agent_node, agent=data_curator_agent, name="DataCurator")
extract_node = functools.partial(agent_node, agent=content_extractor_agent, name="ContentExtractor")

# Update supervisor to route to ContentExtractor
supervisor_agent = create_team_supervisor(
    llm=llm,
    system_prompt=(
        "You are a supervisor tasked with managing a team of agents working on public data collection."
        " Your goal is to decide who acts next based on the current progress. The agents will handle tasks"
        " like link curation, content extraction, and tagging."
        "\n\n"
        "Follow these steps in order:"
        "1. Start with DataCurator to search for links"
        "2. After DataCurator completes, route to ContentExtractor"
        "3. After ContentExtractor completes, route to FINISH"
        "\n\n"
        "Do not skip any steps. Each agent must be called in sequence."
    ),
    members=["DataCurator", "ContentExtractor"]
)

# Create a new StateGraph using the shared state type
data_pipeline_graph = StateGraph(CurationAgentState)

# Add nodes: one for the agent, one for the supervisor
data_pipeline_graph.add_node("DataCurator", curator_node)
data_pipeline_graph.add_node("TeamSupervisor", supervisor_agent)
data_pipeline_graph.add_node("ContentExtractor", extract_node)

# Edge from agent to supervisor
data_pipeline_graph.add_edge("DataCurator", "TeamSupervisor")
data_pipeline_graph.add_edge("ContentExtractor", "TeamSupervisor")

# Conditional edges from supervisor to agents or finish
# Add edges for supervisor routing
data_pipeline_graph.add_conditional_edges(
    "TeamSupervisor",
    lambda state: state["next"],
    {
        "DataCurator": "DataCurator",
        "ContentExtractor": "ContentExtractor",
        "FINISH": END
    }
)

# Set the entry point to the supervisor
data_pipeline_graph.set_entry_point("TeamSupervisor")

# Compile the graph into a runnable DAG
compiled_data_pipeline_graph = data_pipeline_graph.compile()

def enter_chain(message: str):
    return {
        "query": message,
        "messages": [HumanMessage(content=message)]
    }

# Compose it with the compiled graph
data_pipeline_chain = enter_chain | compiled_data_pipeline_graph 