import json
import os

from retriever import retrieve


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

EVAL_PATH = os.path.join(
    BASE_DIR,
    "data",
    "evaluation",
    "retrieval_eval.json"
)


# =========================================================
# LOAD EVALUATION DATA
# =========================================================

def load_evaluation_data():

    with open(
        EVAL_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# =========================================================
# PRECISION@K
# =========================================================

def precision_at_k(
    retrieved_ids,
    relevant_ids,
    k
):

    retrieved = retrieved_ids[:k]

    relevant_count = sum(
        email_id in relevant_ids
        for email_id in retrieved
    )

    return relevant_count / k


# =========================================================
# RECALL@K
# =========================================================

def recall_at_k(
    retrieved_ids,
    relevant_ids,
    k
):

    retrieved = retrieved_ids[:k]

    relevant_count = sum(
        email_id in relevant_ids
        for email_id in retrieved
    )

    if not relevant_ids:
        return 0.0

    return (
        relevant_count
        /
        len(relevant_ids)
    )


# =========================================================
# RECIPROCAL RANK
# =========================================================

def reciprocal_rank(
    retrieved_ids,
    relevant_ids
):

    for rank, email_id in enumerate(
        retrieved_ids,
        start=1
    ):

        if email_id in relevant_ids:

            return 1 / rank

    return 0.0


# =========================================================
# EVALUATE
# =========================================================

def evaluate():

    dataset = load_evaluation_data()

    precision_scores = []
    recall_scores = []
    reciprocal_ranks = []

    for item in dataset:

        query = item["query"]

        relevant_ids = set(
            item["relevant_email_ids"]
        )

        results = retrieve(
            query,
            dense_k=20,
            bm25_k=20,
            final_k=10
        )

        retrieved_ids = []

        for result in results:

            email_id = result[
                "document"
            ].metadata[
                "email_id"
            ]

            if email_id not in retrieved_ids:

                retrieved_ids.append(
                    email_id
                )

        precision = precision_at_k(
            retrieved_ids,
            relevant_ids,
            k=5
        )

        recall = recall_at_k(
            retrieved_ids,
            relevant_ids,
            k=5
        )

        rr = reciprocal_rank(
            retrieved_ids,
            relevant_ids
        )

        precision_scores.append(
            precision
        )

        recall_scores.append(
            recall
        )

        reciprocal_ranks.append(
            rr
        )

        print("\n" + "=" * 70)

        print(
            "Query:",
            query
        )

        print(
            "Relevant:",
            relevant_ids
        )

        print(
            "Retrieved:",
            retrieved_ids
        )

        print(
            "Precision@5:",
            round(precision, 3)
        )

        print(
            "Recall@5:",
            round(recall, 3)
        )

        print(
            "Reciprocal Rank:",
            round(rr, 3)
        )

    # -----------------------------------------------------
    # FINAL METRICS
    # -----------------------------------------------------

    mean_precision = (
        sum(precision_scores)
        /
        len(precision_scores)
    )

    mean_recall = (
        sum(recall_scores)
        /
        len(recall_scores)
    )

    mrr = (
        sum(reciprocal_ranks)
        /
        len(reciprocal_ranks)
    )

    print("\n")
    print("=" * 70)
    print("FINAL RETRIEVAL METRICS")
    print("=" * 70)

    print(
        "Mean Precision@5:",
        round(mean_precision, 4)
    )

    print(
        "Mean Recall@5:",
        round(mean_recall, 4)
    )

    print(
        "MRR:",
        round(mrr, 4)
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    evaluate()