from typing import TypedDict, List
import operator
from langgraph.graph import StateGraph, END
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_ollama import ChatOllama

from langchain_core.prompts import ChatPromptTemplate
from publisher import publish_to_devto

# Define the structure of our shared state
class AgentState(TypedDict):
    topic: str
    research_data: List[str]
    blog_post: str
    # New fields
    review_feedback: str
    revision_count: int

def researcher_agent(state: AgentState):
    print(f"🔎 Researching topic: {state['topic']}...")
    search = DuckDuckGoSearchRun()
    try:
        # Search for the topic
        results = search.invoke(f"latest news and facts about {state['topic']}")
        
        # In a real app, you might want to process 'results' deeper here
        return {"research_data": [results]} 
    except Exception as e:
        print(f"Error in research: {e}")
        return {"research_data": ["No data found due to error."]}

def writer_agent(state: AgentState):
    # Initialize the LLM (Llama 3.1 via Ollama)
    llm = ChatOllama(model="llama3.1:latest", temperature=0.7)
    
    # Check if this is a revision or a first draft
    if state.get("revision_count", 0) > 0:
        print(f"✍️ Rewriting based on feedback (Revision #{state['revision_count']})...")
        prompt_text = """
        You are an engaging tech storyteller, writing for a human audience. 
        Update your previous blog post based strictly on this feedback.
        
        FEEDBACK: {review_feedback}
        ORIGINAL POST: {blog_post}
        
        STYLE GUIDELINES:
        - Write in a natural, conversational tone (like you're talking to a friend).
        - Avoid standard AI transition words like "Moreover," "Furthermore," or "In conclusion."
        - Use rhetorical questions, analogies, and varied sentence lengths.
        - Show personality! It's okay to be slightly opinionated or enthusiastic.
        
        Return ONLY the updated blog post.
        """
        # Increment revision count
        new_count = state["revision_count"] + 1
    else:
        print("✍️ Writing first draft...")
        prompt_text = """
        You are an engaging tech storyteller. Write a blog post about "{topic}" using this research:
        {research_data}
        
        STYLE GUIDELINES:
        - Write in a natural, conversational tone (avoid sounding robotic or academic).
        - Start with a hook that grabs attention immediately.
        - Avoid generic headers and standard AI transition words (e.g., "In conclusion", "Moreover").
        - Use analogies to explain complex concepts.
        - Ask questions to engage the reader.
        - Keep paragraphs relatively short and punchy.
        
        Return ONLY the blog post.
        """
        new_count = 1

    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm
    
    response = chain.invoke({
        "topic": state["topic"],
        "research_data": state.get("research_data", [""]),
        "blog_post": state.get("blog_post", ""),
        "review_feedback": state.get("review_feedback", "")
    })
    
    return {"blog_post": response.content, "revision_count": new_count}

def reviewer_agent(state: AgentState):
    print("🧐 Reviewing the blog post...")
    llm = ChatOllama(model="llama3.1:latest", temperature=0) # Temperature 0 for strict logic
    
    template = """
    You are a senior editor. Review the following blog post.
    
    CRITERIA:
    1. Is it comprehensive?
    2. Is the tone engaging and conversational (Human-like)?
    3. Are there any robotic transitions (e.g., "In conclusion", "Moreover")? If so, flag them.
    4. Does it use varied sentence structure?
    
    BLOG POST:
    {blog_post}
    
    If the post is excellent, reply exactly with: "APPROVE"
    If it needs work, list specific critique and improvements needed.
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({"blog_post": state["blog_post"]})
    
    return {"review_feedback": response.content}

def publisher_agent(state: AgentState):
    print("🚀 Publishing blog post to Dev.to...")
    
    # Extract title (simple logic: first line of blog or generic)
    blog_content = state['blog_post']
    title = state['topic'] 
    
    # Push to Dev.to
    url = publish_to_devto(title, blog_content, tags=["ai", "agents", "langgraph"])
    
    # We can store the URL in the state if we want to show it to the user later
    if url:
        return {"review_feedback": f"PUBLISHED: {url}"}
    return {"review_feedback": "Failed to publish."}

def router(state: AgentState):
    feedback = state["review_feedback"]
    count = state["revision_count"]
    
    # Safety Valve: Stop after 3 revisions to prevent infinite costs/loops
    if count >= 3:
        print("⚠️ Max revisions reached. Stopping.")
        return END
        
    if "APPROVE" in feedback:
        print("✅ Editor approved the post!")
        return "Publisher"
    else:
        print("❌ Editor requested changes. Sending back to Writer...")
        return "Writer"

# Initialize the Graph with our State structure
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("Researcher", researcher_agent)
workflow.add_node("Writer", writer_agent)
workflow.add_node("Reviewer", reviewer_agent)
workflow.add_node("Publisher", publisher_agent)

# Set Entry Point
workflow.set_entry_point("Researcher")

# Normal Linear Edges
workflow.add_edge("Researcher", "Writer")
workflow.add_edge("Writer", "Reviewer")

# Conditional Edge (The Loop)
# After "Reviewer", look at "router" to decide: Go to "Writer" OR "END"
workflow.add_conditional_edges(
    "Reviewer", 
    router, 
    {
        "Writer": "Writer", 
        "Publisher": "Publisher",
        END: END
    }
)

# Add edge from Publisher to END
workflow.add_edge("Publisher", END)

app = workflow.compile()

if __name__ == "__main__":
    # Define the initial input
    input_topic = "The Impact of Quantum Computing on AI"
    
    print(f"🚀 Starting Multi-Agent System for: {input_topic}")
    
    inputs = {
        "topic": input_topic,
        "research_data": [],
        "blog_post": "",
        "review_feedback": "",
        "revision_count": 0
    }
    
    result = app.invoke(inputs)
    
    print("\n" + "="*50)
    print("FINAL POLISHED POST:")
    print("="*50 + "\n")
    print(result["blog_post"])
