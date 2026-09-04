import os
import pickle
import hashlib
from typing import List, Dict, Any

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = "C:\\code\\demo\\AI_agent_email\\vector_stores"

VECTORSTORE_DIR = os.path.join(
    BASE_DIR,
    "vector_stores"
)

DEFAULT_STORE = "read_and_replied"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

RERANKER_MODEL = "BAAI/bge-reranker-base"

BM25_FILE = "bm25.pkl"
CHUNKS_FILE = "chunks.pkl"


# ============================================================
# MODELS
# ============================================================

print("Loading embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)

print("Embedding model loaded.")


print("Loading reranker...")

reranker = CrossEncoder(
    RERANKER_MODEL
)

print("Reranker loaded.")


# ============================================================
# PATH HELPERS
# ============================================================

def get_store_path(store_name: str) -> str:
    """
    Return the directory containing a vector store.
    """

    return os.path.join(
        VECTORSTORE_DIR,
        store_name
    )


def get_faiss_path(store_name: str) -> str:
    return get_store_path(store_name)


def get_chunks_path(store_name: str) -> str:
    return os.path.join(
        get_store_path(store_name),
        CHUNKS_FILE
    )


def get_bm25_path(store_name: str) -> str:
    return os.path.join(
        get_store_path(store_name),
        BM25_FILE
    )


# ============================================================
# LOAD FAISS
# ============================================================

def load_faiss(
    store_name: str = DEFAULT_STORE
):
    """
    Load the existing FAISS vector store.
    """

    store_path = get_faiss_path(store_name)

    if not os.path.exists(store_path):
        raise FileNotFoundError(
            f"FAISS vector store not found:\n{store_path}\n\n"
            f"Run vector_store.py first."
        )

    vectorstore = FAISS.load_local(
        store_path,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vectorstore


# ============================================================
# LOAD EXACT CHUNKS USED BY FAISS
# ============================================================

def load_chunks(
    store_name: str = DEFAULT_STORE
) -> List[Document]:
    """
    Load the exact chunks that were used to build FAISS.

    This is important because BM25 must operate on the same
    chunks as FAISS.
    """

    chunks_path = get_chunks_path(store_name)

    if not os.path.exists(chunks_path):
        raise FileNotFoundError(
            f"chunks.pkl not found:\n{chunks_path}\n\n"
            f"Rebuild the vector store using the updated "
            f"vector_store.py."
        )

    with open(
        chunks_path,
        "rb"
    ) as file:

        chunks = pickle.load(file)

    return chunks


# ============================================================
# BUILD BM25
# ============================================================

def build_bm25(
    store_name: str = DEFAULT_STORE
):
    """
    Build BM25 using exactly the same chunks as FAISS.
    """

    print("\n" + "=" * 60)
    print("BUILDING BM25")
    print("=" * 60)

    chunks = load_chunks(store_name)

    print(
        f"Store: {store_name}"
    )

    print(
        f"Total chunks: {len(chunks)}"
    )

    tokenized_chunks = []

    for chunk in chunks:

        text = chunk.page_content

        tokens = text.lower().split()

        tokenized_chunks.append(tokens)

    bm25 = BM25Okapi(
        tokenized_chunks
    )

    bm25_path = get_bm25_path(store_name)

    with open(
        bm25_path,
        "wb"
    ) as file:

        pickle.dump(
            {
                "bm25": bm25,
                "chunks": chunks
            },
            file
        )

    print(
        f"BM25 saved to:\n{bm25_path}"
    )

    return bm25, chunks


# ============================================================
# LOAD BM25
# ============================================================

def load_bm25(
    store_name: str = DEFAULT_STORE
):
    """
    Load persisted BM25 index.
    """

    bm25_path = get_bm25_path(store_name)

    if not os.path.exists(bm25_path):

        print(
            "BM25 index does not exist."
        )

        print(
            "Building BM25..."
        )

        return build_bm25(
            store_name
        )

    with open(
        bm25_path,
        "rb"
    ) as file:

        data = pickle.load(file)

    return (
        data["bm25"],
        data["chunks"]
    )


# ============================================================
# DOCUMENT IDENTIFIER
# ============================================================

def get_document_key(
    document: Document
):
    """
    Generate a stable identifier for a chunk.

    email_id identifies the email/conversation.
    conversation_type distinguishes original/reply.
    content_hash distinguishes chunks.
    """

    metadata = document.metadata

    email_id = metadata.get(
        "email_id",
        ""
    )

    conversation_type = metadata.get(
        "conversation_type",
        ""
    )

    content_hash = hashlib.md5(
        document.page_content.encode(
            "utf-8"
        )
    ).hexdigest()

    return (
        email_id,
        conversation_type,
        content_hash
    )


# ============================================================
# DENSE SEARCH
# ============================================================

def dense_search(
    query: str,
    k: int = 10,
    store_name: str = DEFAULT_STORE
) -> List[Dict[str, Any]]:
    """
    Semantic retrieval using FAISS.
    """

    vectorstore = load_faiss(
        store_name
    )

    results = vectorstore.similarity_search_with_score(
        query,
        k=k
    )

    output = []

    for rank, item in enumerate(
        results,
        start=1
    ):

        document, distance = item

        output.append(
            {
                "document": document,

                "dense_score": float(
                    distance
                ),

                "dense_rank": rank,

                "bm25_score": None,

                "bm25_rank": None,

                "hybrid_score": 0.0,

                "rerank_score": None
            }
        )

    return output


# ============================================================
# BM25 SEARCH
# ============================================================

def bm25_search(
    query: str,
    k: int = 10,
    store_name: str = DEFAULT_STORE
) -> List[Dict[str, Any]]:
    """
    Lexical retrieval using BM25.
    """

    bm25, chunks = load_bm25(
        store_name
    )

    query_tokens = query.lower().split()

    scores = bm25.get_scores(
        query_tokens
    )

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )

    output = []

    rank = 0

    for index in ranked_indices:

        score = scores[index]

        # Skip documents with zero BM25 relevance.
        if score <= 0:
            continue

        rank += 1

        document = chunks[index]

        output.append(
            {
                "document": document,

                "dense_score": None,

                "dense_rank": None,

                "bm25_score": float(
                    score
                ),

                "bm25_rank": rank,

                "hybrid_score": 0.0,

                "rerank_score": None
            }
        )

        if rank >= k:
            break

    return output


# ============================================================
# RECIPROCAL RANK FUSION
# ============================================================

def reciprocal_rank_fusion(
    dense_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    rrf_k: int = 60
) -> List[Dict[str, Any]]:
    """
    Combine dense and BM25 rankings using RRF.

    RRF score:

        1 / (rrf_k + rank)

    If a document appears in both systems,
    the scores are added.
    """

    candidates = {}

    # --------------------------------------------------------
    # Add dense results
    # --------------------------------------------------------

    for result in dense_results:

        document = result["document"]

        key = get_document_key(
            document
        )

        if key not in candidates:

            candidates[key] = {
                "document": document,

                "dense_score": None,

                "dense_rank": None,

                "bm25_score": None,

                "bm25_rank": None,

                "hybrid_score": 0.0,

                "rerank_score": None
            }

        candidates[key][
            "dense_score"
        ] = result["dense_score"]

        candidates[key][
            "dense_rank"
        ] = result["dense_rank"]

        candidates[key][
            "hybrid_score"
        ] += 1 / (
            rrf_k + result["dense_rank"]
        )

    # --------------------------------------------------------
    # Add BM25 results
    # --------------------------------------------------------

    for result in bm25_results:

        document = result["document"]

        key = get_document_key(
            document
        )

        if key not in candidates:

            candidates[key] = {
                "document": document,

                "dense_score": None,

                "dense_rank": None,

                "bm25_score": None,

                "bm25_rank": None,

                "hybrid_score": 0.0,

                "rerank_score": None
            }

        candidates[key][
            "bm25_score"
        ] = result["bm25_score"]

        candidates[key][
            "bm25_rank"
        ] = result["bm25_rank"]

        candidates[key][
            "hybrid_score"
        ] += 1 / (
            rrf_k + result["bm25_rank"]
        )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    results = list(
        candidates.values()
    )

    results.sort(
        key=lambda x: x["hybrid_score"],
        reverse=True
    )

    return results


# ============================================================
# HYBRID SEARCH
# ============================================================

def hybrid_search(
    query: str,
    dense_k: int = 10,
    bm25_k: int = 10,
    rrf_k: int = 60,
    candidate_k: int = 20,
    store_name: str = DEFAULT_STORE
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval:

        FAISS
          +
        BM25
          ↓
        RRF
          ↓
        candidates
    """

    dense_results = dense_search(
        query=query,
        k=dense_k,
        store_name=store_name
    )

    bm25_results = bm25_search(
        query=query,
        k=bm25_k,
        store_name=store_name
    )

    fused_results = reciprocal_rank_fusion(
        dense_results=dense_results,
        bm25_results=bm25_results,
        rrf_k=rrf_k
    )

    return fused_results[
        :candidate_k
    ]


# ============================================================
# RERANKING
# ============================================================

def rerank(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Rerank hybrid candidates using a cross-encoder.
    """

    if not candidates:
        return []

    pairs = []

    for candidate in candidates:

        document = candidate[
            "document"
        ]

        pairs.append(
            (
                query,
                document.page_content
            )
        )

    scores = reranker.predict(
        pairs
    )

    for candidate, score in zip(
        candidates,
        scores
    ):

        candidate[
            "rerank_score"
        ] = float(score)

    candidates.sort(
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return candidates[
        :top_k
    ]


# ============================================================
# COMPLETE RETRIEVAL PIPELINE
# ============================================================
def deduplicate_results(
    results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Remove duplicate historical results.

    Two results are considered duplicates when they have:
    1. The same email_id, or
    2. The same normalized content.

    Since results are already sorted by reranker score,
    the highest-ranked version is retained.
    """

    unique_results = []

    seen_email_ids = set()
    seen_contents = set()

    for result in results:

        document = result["document"]
        metadata = document.metadata

        email_id = metadata.get(
            "email_id"
        )

        content = document.page_content

        normalized_content = " ".join(
            content.lower().split()
        )

        # Same email
        if email_id in seen_email_ids:
            continue

        # Same content
        if normalized_content in seen_contents:
            continue

        seen_email_ids.add(
            email_id
        )

        seen_contents.add(
            normalized_content
        )

        unique_results.append(
            result
        )

    return unique_results

def retrieve(
    query: str,
    dense_k: int = 10,
    bm25_k: int = 10,
    candidate_k: int = 20,
    final_k: int = 5,
    store_name: str = DEFAULT_STORE
):
    """
    Complete retrieval pipeline:

        FAISS
          +
        BM25
          ↓
        RRF
          ↓
        Candidate generation
          ↓
        BGE reranker
          ↓
        Deduplication
          ↓
        Final results
    """

    candidates = hybrid_search(
        query=query,
        dense_k=dense_k,
        bm25_k=bm25_k,
        candidate_k=candidate_k,
        store_name=store_name
    )

    # Rerank more candidates than we ultimately need.
    reranked = rerank(
        query=query,
        candidates=candidates,
        top_k=candidate_k
    )

    # Remove duplicate emails/content.
    unique_results = deduplicate_results(
        reranked
    )

    # Return only final K.
    return unique_results[
        :final_k
    ]


# ============================================================
# UNIQUE EMAIL IDS
# ============================================================

def get_unique_email_ids(
    results: List[Dict[str, Any]]
) -> List[Any]:
    """
    Convert chunk-level retrieval into email-level retrieval.

    This is important for evaluation because multiple chunks
    can belong to the same email.
    """

    email_ids = []

    seen = set()

    for result in results:

        metadata = result[
            "document"
        ].metadata

        email_id = metadata.get(
            "email_id"
        )

        if email_id is None:
            continue

        if email_id not in seen:

            seen.add(
                email_id
            )

            email_ids.append(
                email_id
            )

    return email_ids


# ============================================================
# PRINT RESULTS
# ============================================================

def print_results(
    results: List[Dict[str, Any]],
    title: str = "RESULTS"
):

    print("\n")
    print("=" * 80)
    print(title)
    print("=" * 80)

    if not results:

        print(
            "No results found."
        )

        return

    for i, result in enumerate(
        results,
        start=1
    ):

        document = result[
            "document"
        ]

        metadata = document.metadata

        print(
            f"\nRESULT #{i}"
        )

        print(
            "-" * 80
        )

        print(
            "Email ID:",
            metadata.get(
                "email_id"
            )
        )

        print(
            "Conversation Type:",
            metadata.get(
                "conversation_type",
                "N/A"
            )
        )

        print(
            "Source:",
            metadata.get(
                "source",
                "N/A"
            )
        )

        print(
            "Sender:",
            metadata.get(
                "sender",
                "N/A"
            )
        )

        print(
            "Subject:",
            metadata.get(
                "subject",
                "N/A"
            )
        )

        print(
            "Dense Rank:",
            result.get(
                "dense_rank"
            )
        )

        print(
            "BM25 Rank:",
            result.get(
                "bm25_rank"
            )
        )

        print(
            "Hybrid Score:",
            result.get(
                "hybrid_score"
            )
        )

        print(
            "Rerank Score:",
            result.get(
                "rerank_score"
            )
        )

        print(
            "\nContent:"
        )

        print(
            document.page_content[:1000]
        )


# ============================================================
# TEST FAISS
# ============================================================

def test_dense_search(
    query: str,
    store_name: str = DEFAULT_STORE
):
    """
    Test FAISS retrieval.
    """

    print("\n")
    print("=" * 80)
    print("TEST 1: FAISS DENSE SEARCH")
    print("=" * 80)

    results = dense_search(
        query=query,
        k=5,
        store_name=store_name
    )

    print_results(
        results,
        "FAISS RESULTS"
    )

    return results


# ============================================================
# TEST BM25
# ============================================================

def test_bm25_search(
    query: str,
    store_name: str = DEFAULT_STORE
):
    """
    Test BM25 retrieval.
    """

    print("\n")
    print("=" * 80)
    print("TEST 2: BM25 SEARCH")
    print("=" * 80)

    results = bm25_search(
        query=query,
        k=5,
        store_name=store_name
    )

    print_results(
        results,
        "BM25 RESULTS"
    )

    return results


# ============================================================
# TEST HYBRID
# ============================================================

def test_hybrid_search(
    query: str,
    store_name: str = DEFAULT_STORE
):
    """
    Test FAISS + BM25 + RRF.
    """

    print("\n")
    print("=" * 80)
    print("TEST 3: HYBRID SEARCH")
    print("=" * 80)

    results = hybrid_search(
        query=query,
        dense_k=10,
        bm25_k=10,
        candidate_k=10,
        store_name=store_name
    )

    print_results(
        results,
        "HYBRID RESULTS"
    )

    return results


# ============================================================
# TEST RERANKER
# ============================================================

def test_reranker(
    query: str,
    store_name: str = DEFAULT_STORE
):
    """
    Test complete hybrid + reranking pipeline.
    """

    print("\n")
    print("=" * 80)
    print("TEST 4: HYBRID + RERANKER")
    print("=" * 80)

    results = retrieve(
        query=query,
        dense_k=10,
        bm25_k=10,
        candidate_k=10,
        final_k=5,
        store_name=store_name
    )

    print_results(
        results,
        "FINAL RERANKED RESULTS"
    )

    return results


# ============================================================
# FULL SYSTEM TEST
# ============================================================

def run_full_test(
    store_name: str = DEFAULT_STORE
):
    """
    Run all retrieval components.

    This verifies:

        1. FAISS exists
        2. chunks.pkl exists
        3. BM25 exists/builds
        4. FAISS retrieval works
        5. BM25 retrieval works
        6. Hybrid retrieval works
        7. Reranker works
    """

    print("\n")
    print("=" * 80)
    print("RETRIEVAL SYSTEM TEST")
    print("=" * 80)

    print(
        f"Store: {store_name}"
    )

    # --------------------------------------------------------
    # 1. Check paths
    # --------------------------------------------------------

    store_path = get_store_path(
        store_name
    )

    chunks_path = get_chunks_path(
        store_name
    )

    bm25_path = get_bm25_path(
        store_name
    )

    print("\nChecking files...")

    print(
        "Vector store:",
        store_path
    )

    print(
        "FAISS directory exists:",
        os.path.exists(store_path)
    )

    print(
        "chunks.pkl exists:",
        os.path.exists(chunks_path)
    )

    print(
        "bm25.pkl exists:",
        os.path.exists(bm25_path)
    )

    if not os.path.exists(
        store_path
    ):

        raise FileNotFoundError(
            "FAISS vector store does not exist."
        )

    if not os.path.exists(
        chunks_path
    ):

        raise FileNotFoundError(
            "chunks.pkl does not exist. "
            "Rebuild vector_store.py first."
        )

    # --------------------------------------------------------
    # 2. Load chunks
    # --------------------------------------------------------

    chunks = load_chunks(
        store_name
    )

    print(
        f"\nLoaded {len(chunks)} chunks."
    )

    if len(chunks) == 0:

        raise ValueError(
            "No chunks found."
        )

    # --------------------------------------------------------
    # 3. Build/load BM25
    # --------------------------------------------------------

    bm25, bm25_chunks = load_bm25(
        store_name
    )

    if len(bm25_chunks) != len(
        chunks
    ):

        raise ValueError(
            "BM25 chunks and FAISS chunks "
            "do not have the same length."
        )

    print(
        "BM25 chunk count matches FAISS chunks."
    )

    # --------------------------------------------------------
    # Test query
    # --------------------------------------------------------

    query = (
        "Python coding assessment"
    )

    print(
        f"\nTest query:\n{query}"
    )

    # --------------------------------------------------------
    # 4. Dense
    # --------------------------------------------------------

    dense_results = test_dense_search(
        query,
        store_name
    )

    assert len(
        dense_results
    ) > 0, "FAISS returned no results."

    print(
        "\nFAISS TEST PASSED"
    )

    # --------------------------------------------------------
    # 5. BM25
    # --------------------------------------------------------

    bm25_results = test_bm25_search(
        query,
        store_name
    )

    print(
        "\nBM25 TEST PASSED"
    )

    # --------------------------------------------------------
    # 6. Hybrid
    # --------------------------------------------------------

    hybrid_results = test_hybrid_search(
        query,
        store_name
    )

    assert len(
        hybrid_results
    ) > 0, "Hybrid search returned no results."

    print(
        "\nHYBRID TEST PASSED"
    )

    # --------------------------------------------------------
    # 7. Reranker
    # --------------------------------------------------------

    final_results = test_reranker(
        query,
        store_name
    )

    assert len(
        final_results
    ) > 0, "Reranker returned no results."

    print(
        "\nRERANKER TEST PASSED"
    )

    # --------------------------------------------------------
    # 8. Email IDs
    # --------------------------------------------------------

    email_ids = get_unique_email_ids(
        final_results
    )

    print(
        "\nUnique retrieved email IDs:"
    )

    print(
        email_ids
    )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("ALL RETRIEVAL TESTS PASSED")
    print("=" * 80)


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    import sys

    # --------------------------------------------------------
    # Build BM25
    # --------------------------------------------------------

    if "--build-bm25" in sys.argv:

        build_bm25(
            DEFAULT_STORE
        )

    # --------------------------------------------------------
    # Full test
    # --------------------------------------------------------

    elif "--test" in sys.argv:

        run_full_test(
            DEFAULT_STORE
        )

    # --------------------------------------------------------
    # Simple manual query
    # --------------------------------------------------------

    else:

        query = input(
            "\nEnter your search query: "
        ).strip()

        if not query:

            print(
                "Query cannot be empty."
            )

        else:

            results = retrieve(
                query=query,
                dense_k=10,
                bm25_k=10,
                candidate_k=20,
                final_k=5,
                store_name=DEFAULT_STORE
            )

            print_results(
                results,
                "FINAL RETRIEVAL RESULTS"
            )