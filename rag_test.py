from vector_stores.retriever import retrieve_context
from llm import analyze_email, generate_reply


# ---------------------------------------------------------
# CURRENT EMAIL
# ---------------------------------------------------------

current_email = {

    "sender": "hr@company.com",

    "subject": "Python Coding Assessment",

    "date": "2026-09-04",

    "body": """
    Please complete the Python coding assessment
    and submit your solution through the portal.
    """
}


# ---------------------------------------------------------
# STEP 1: ANALYZE
# ---------------------------------------------------------

analysis = analyze_email(
    current_email
)

print("\n")
print("=" * 70)
print("STEP 1 — EMAIL ANALYSIS")
print("=" * 70)

print("Priority:", analysis.priority)

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


# ---------------------------------------------------------
# STEP 2: RETRIEVE HISTORY
# ---------------------------------------------------------

context = retrieve_context(
    current_email,
    k=5
)

print("\n")
print("=" * 70)
print("STEP 2 — RETRIEVED CONTEXT")
print("=" * 70)

print(context)


# ---------------------------------------------------------
# STEP 3: GENERATE REPLY
# ---------------------------------------------------------

if analysis.requires_response:

    reply = generate_reply(
        current_email,
        context
    )

    print("\n")
    print("=" * 70)
    print("STEP 3 — GENERATED REPLY")
    print("=" * 70)

    print(reply)

else:

    print("\nNo reply required.")