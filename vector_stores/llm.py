import os
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# LLM
# ---------------------------------------------------------

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)


# ---------------------------------------------------------
# STRUCTURED OUTPUT
# ---------------------------------------------------------

class EmailAnalysis(BaseModel):

    priority: Literal[
        "HIGH",
        "MEDIUM",
        "LOW"
    ] = Field(
        description="Priority of the email"
    )

    requires_response: bool = Field(
        description="Whether the email requires a response"
    )

    summary: str = Field(
        description="Short summary of the email"
    )

    action_items: list[str] = Field(
        description="Actions that the user needs to take"
    )


structured_llm = llm.with_structured_output(
    EmailAnalysis
)


# ---------------------------------------------------------
# EMAIL ANALYSIS PROMPT
# ---------------------------------------------------------

analysis_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an intelligent email triage assistant.

Analyze the incoming email and determine:

1. Priority
2. Whether a response is required
3. A concise summary
4. Action items

Priority rules:

HIGH:
- Urgent requests
- Deadlines within 24 hours
- Customer escalation
- Production or critical business issue
- Payment issue
- Legal or compliance issue
- Executive communication
- Explicit urgent request

MEDIUM:
- Requires user action
- Important question
- Meeting request
- Normal business request
- Follow-up requiring a response

LOW:
- FYI messages
- Newsletters
- Marketing emails
- General announcements
- Messages requiring no action

Do not classify based only on keywords.
Consider the complete meaning of the email.

Return action_items as an empty list if there are no actions.
"""
        ),
        (
            "human",
            """
Analyze this email:

From:
{sender}

Subject:
{subject}

Date:
{date}

Body:
{body}
"""
        )
    ]
)


# ---------------------------------------------------------
# ANALYZE EMAIL
# ---------------------------------------------------------

def analyze_email(email):

    chain = analysis_prompt | structured_llm

    result = chain.invoke(
        {
            "sender": email.get("sender", ""),
            "subject": email.get("subject", ""),
            "date": email.get("date", ""),
            "body": email.get("body", "")
        }
    )

    return result


# ---------------------------------------------------------
# REPLY GENERATION PROMPT
# ---------------------------------------------------------

reply_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a professional email assistant.

Your task is to generate a reply to the CURRENT EMAIL.

You may use HISTORICAL EMAILS as examples of:
- How the user previously responded
- The user's communication style
- Relevant factual information

Rules:

1. Never invent facts.
2. Never claim that an action has been completed unless the
   current email or historical context confirms it.
3. Never expose information from unrelated historical emails.
4. Do not copy confidential information unnecessarily.
5. If required information is missing, ask the sender for it.
6. Do not respond to automated or no-reply emails unless a response
   is clearly appropriate.
7. Keep the response concise and professional.
8. Do not mention that you are an AI.
9. Do not mention the historical emails.
10. Return only the email body.
"""
        ),
        (
            "human",
            """
CURRENT EMAIL
=============

From:
{sender}

Subject:
{subject}

Date:
{date}

Body:
{body}


HISTORICAL EMAIL CONTEXT
========================

{context}


Generate the best possible reply to the CURRENT EMAIL.
"""
        )
    ]
)


# ---------------------------------------------------------
# GENERATE REPLY
# ---------------------------------------------------------

def generate_reply(
    email,
    context
):

    chain = reply_prompt | llm

    result = chain.invoke(
        {
            "sender": email.get("sender", ""),
            "subject": email.get("subject", ""),
            "date": email.get("date", ""),
            "body": email.get("body", ""),
            "context": context
        }
    )

    return result.content.strip()


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    email = {
        "sender": "hr@company.com",
        "subject": "Python Coding Assessment",
        "date": "2026-09-04",
        "body": """
Please complete the Python coding assessment
and submit your solution through the portal.
"""
    }

    # ---------------------------------------------
    # ANALYSIS
    # ---------------------------------------------

    analysis = analyze_email(email)

    print("\n")
    print("=" * 70)
    print("EMAIL ANALYSIS")
    print("=" * 70)

    print(
        "Priority:",
        analysis.priority
    )

    print(
        "Requires Response:",
        analysis.requires_response
    )

    print(
        "Summary:",
        analysis.summary
    )

    print(
        "Action Items:",
        analysis.action_items
    )

    # ---------------------------------------------
    # REPLY
    # ---------------------------------------------

    historical_context = """
Historical Email 1

Original Email:
Please complete the Python coding task.

User's Previous Reply:
I have completed and submitted the coding task.
"""

    reply = generate_reply(
        email,
        historical_context
    )

    print("\n")
    print("=" * 70)
    print("GENERATED REPLY")
    print("=" * 70)

    print(reply)