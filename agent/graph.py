from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from vector_stores.llm import analyze_email, generate_reply
from vector_stores.retriever import retrieve


class EmailState(TypedDict):

    email: dict

    priority: str
    summary: str
    action_items: list[str]
    requires_response: bool

    retrieved_context: str
    draft_reply: str

    approval_status: str
    final_reply: str

    send_status: str
def generate_reply_node(state: EmailState):

    email = state["email"]
    context = state["retrieved_context"]

    draft = generate_reply(
        email=email,
        context=context
    )

    return {
        "draft_reply": draft
    }
def human_approval_node(state: EmailState):

    approval = interrupt({
        "type": "email_approval",
        "message": "Please review the generated reply.",
        "email": state["email"],
        "draft_reply": state["draft_reply"],
    })

    return {
        "approval_status": approval["status"],
        "final_reply": approval.get(
            "edited_reply",
            state["draft_reply"]
        )
    }
def approval_router(state: EmailState):

    if state["approval_status"] == "approve":
        return END

    if state["approval_status"] == "edit":
        return END

    if state["approval_status"] == "reject":
        return END

    return END
def retrieve_context_node(state: EmailState):

    email = state["email"]

    query = f"""
    Subject: {email.get("subject", "")}

    Body:
    {email.get("body", "")}
    """

    results = retrieve(
        query=query,
        store_name="read_and_replied",
        final_k=5
    )

    context_parts = []

    for result in results:

        document = result["document"]

        context_parts.append(
            document.page_content
        )

    context = "\n\n---\n\n".join(context_parts)

    return {
        "retrieved_context": context
    }
def should_respond(state: EmailState):

    if state["requires_response"]:
        return "retrieve_context"

    return END
def analyze_email_node(state: EmailState):

    email = state["email"]

    result = analyze_email(email)

    return {
        "priority": result.priority,
        "summary": result.summary,
        "action_items": result.action_items,
        "requires_response": result.requires_response,
    }
builder = StateGraph(EmailState)
builder.add_node(
    "analyze_email",
    analyze_email_node
)

builder.add_node(
    "retrieve_context",
    retrieve_context_node
)

builder.add_node(
    "generate_reply",
    generate_reply_node
)
builder.add_node(
    "human_approval",
    human_approval_node
)

builder.add_edge(
    START,
    "analyze_email"
)
builder.add_conditional_edges(
    "analyze_email",
    should_respond
)
builder.add_edge(
    "retrieve_context",
    "generate_reply"
)

builder.add_edge(
    "generate_reply",
    "human_approval"
)

builder.add_conditional_edges(
    "human_approval",
    approval_router
)
graph = builder.compile()

if __name__ == "__main__":

    email = {
        "sender": "nicolas@example.com",
        "subject": "Python Coding Assessment",
        "date": "2026-09-04",
        "body": """
        Hi,

        I completed the Python coding assessment.
        However, when I tried to submit it, the system
        showed an assessment incomplete message.

        Could you please check this issue?

        Regards,
        Nicolas
        """
    }

    initial_state = {
        "email": email,

        "priority": "",
        "summary": "",
        "action_items": [],
        "requires_response": False,

        "retrieved_context": "",
        "draft_reply": "",

        "approval_status": "",
        "final_reply": "",

        "send_status": "",
    }

    config = {
    "configurable": {
        "thread_id": "email-001"
    }
}

    result = graph.invoke(
        initial_state,
        config
    )

    print("\n==============================")
    print("EMAIL ANALYSIS")
    print("==============================")

    print("Priority:", result["priority"])
    print("Summary:", result["summary"])
    print("Requires Response:", result["requires_response"])
    print("Action Items:", result["action_items"])

    print("\n==============================")
    print("RETRIEVED CONTEXT")
    print("==============================")

    print(result["retrieved_context"])

    print("\n==============================")
    print("DRAFT REPLY")
    print("==============================")

    print(result["draft_reply"])