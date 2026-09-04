import json
import os
import pickle
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = r"C:\code\demo\AI_agent_email\data\output"
VECTORSTORE_DIR = os.path.join(BASE_DIR, "vector_stores")


# ---------------------------------------------------------
# EMBEDDING MODEL
# ---------------------------------------------------------

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ---------------------------------------------------------
# TEXT SPLITTER
# ---------------------------------------------------------

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""]
)


# ---------------------------------------------------------
# LOAD JSON
# ---------------------------------------------------------

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# ---------------------------------------------------------
# CREATE NORMAL EMAIL DOCUMENTS
# ---------------------------------------------------------

def create_normal_documents(emails, source):
    documents = []

    for email_id, email in enumerate(emails):

        content = (
            f"Subject: {email.get('subject', '')}\n\n"
            f"{email.get('body', '')}"
        )

        metadata = {
            "email_id": email_id,
            "source": source,
            "sender": email.get("sender", ""),
            "subject": email.get("subject", ""),
            "date": email.get("date", ""),
        }

        documents.append(
            Document(
                page_content=content,
                metadata=metadata
            )
        )

    return documents


# ---------------------------------------------------------
# CREATE READ + REPLIED DOCUMENTS
# ---------------------------------------------------------

def create_replied_documents(emails):
    documents = []

    for email_id, email in enumerate(emails):

        # ---------------------------------------------
        # ORIGINAL EMAIL
        # ---------------------------------------------

        original_content = (
            f"Subject: {email.get('subject', '')}\n\n"
            f"{email.get('body', '')}"
        )

        original_metadata = {
            "email_id": email_id,
            "source": "read_and_replied",
            "conversation_type": "original",
            "sender": email.get("sender", ""),
            "subject": email.get("subject", ""),
            "date": email.get("date", ""),
        }

        documents.append(
            Document(
                page_content=original_content,
                metadata=original_metadata
            )
        )

        # ---------------------------------------------
        # USER REPLY
        # ---------------------------------------------

        reply = email.get("reply")

        if reply:

            reply_content = (
                f"Subject: {reply.get('subject', '')}\n\n"
                f"{reply.get('body', '')}"
            )

            reply_metadata = {
                "email_id": email_id,
                "source": "read_and_replied",
                "conversation_type": "reply",
                "sender": reply.get("sender", ""),
                "subject": reply.get("subject", ""),
                "date": reply.get("date", ""),
            }

            documents.append(
                Document(
                    page_content=reply_content,
                    metadata=reply_metadata
                )
            )

    return documents


# ---------------------------------------------------------
# CHUNK DOCUMENTS
# ---------------------------------------------------------

def chunk_documents(documents):

    chunks = text_splitter.split_documents(documents)

    return chunks


# ---------------------------------------------------------
# BUILD VECTOR STORE
# ---------------------------------------------------------

def build_vector_store(documents, store_name):

    print(f"\nBuilding vector store: {store_name}")

    print(f"Original documents: {len(documents)}")

    chunks = chunk_documents(documents)

    print(f"Total chunks: {len(chunks)}")

    store_path = os.path.join(
        VECTORSTORE_DIR,
        store_name
    )

    os.makedirs(
        store_path,
        exist_ok=True
    )

    # ---------------------------------------------
    # SAVE CHUNKS
    # ---------------------------------------------

    chunks_path = os.path.join(
        store_path,
        "chunks.pkl"
    )

    with open(
        chunks_path,
        "wb"
    ) as file:

        pickle.dump(
            chunks,
            file
        )

    # ---------------------------------------------
    # CREATE FAISS
    # ---------------------------------------------

    vectorstore = FAISS.from_documents(
        chunks,
        embeddings
    )

    vectorstore.save_local(
        store_path
    )

    print(
        f"Vector store saved to: {store_path}"
    )

    print(
        f"Chunks saved to: {chunks_path}"
    )

    return vectorstore


# ---------------------------------------------------------
# BUILD ALL THREE STORES
# ---------------------------------------------------------

def build_all_vectorstores():

    # ---------------------------------------------
    # UNREAD
    # ---------------------------------------------

    unread_emails = load_json(
        "unread_emails.json"
    )

    unread_documents = create_normal_documents(
        unread_emails,
        "unread"
    )

    build_vector_store(
        unread_documents,
        "unread"
    )

    # ---------------------------------------------
    # READ
    # ---------------------------------------------

    read_emails = load_json(
        "read_emails.json"
    )

    read_documents = create_normal_documents(
        read_emails,
        "read"
    )

    build_vector_store(
        read_documents,
        "read"
    )

    # ---------------------------------------------
    # READ + REPLIED
    # ---------------------------------------------

    replied_emails = load_json(
        "read_and_replied_emails.json"
    )

    replied_documents = create_replied_documents(
        replied_emails
    )

    build_vector_store(
        replied_documents,
        "read_and_replied"
    )


# ---------------------------------------------------------
# LOAD VECTOR STORE
# ---------------------------------------------------------

def load_vector_store(store_name):

    store_path = os.path.join(
        VECTORSTORE_DIR,
        store_name
    )

    vectorstore = FAISS.load_local(
        store_path,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vectorstore


# ---------------------------------------------------------
# TEST RETRIEVAL
# ---------------------------------------------------------

def test_search(store_name, query, k=3):

    vectorstore = load_vector_store(store_name)

    results = vectorstore.similarity_search(
        query,
        k=k
    )

    print("\n" + "=" * 70)
    print(f"SEARCH: {query}")
    print(f"STORE: {store_name}")
    print("=" * 70)

    for i, doc in enumerate(results, start=1):

        print(f"\nRESULT {i}")

        print("Metadata:")
        print(doc.metadata)

        print("\nContent:")
        print(doc.page_content)

        print("-" * 70)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

if __name__ == "__main__":

    build_all_vectorstores()

    # Example tests

    test_search(
        "read_and_replied",
        "I accepted an internship offer",
        k=3
    )

    test_search(
        "read_and_replied",
        "I completed a coding test",
        k=3
    )

    test_search(
        "read_and_replied",
        "I am facing an issue and attached a screenshot",
        k=3
    )