from vector_store import create_vector_store


DATA_DIR = "data/output"


def main():

    print("=" * 70)
    print("BUILDING EMAIL VECTOR STORES")
    print("=" * 70)

    # ------------------------------------------------
    # 1. UNREAD EMAILS
    # ------------------------------------------------

    create_vector_store(
        json_path=f"{DATA_DIR}/unread_emails.json",
        store_path="vector_stores/unread",
        source="unread"
    )

    # ------------------------------------------------
    # 2. READ EMAILS
    # ------------------------------------------------

    create_vector_store(
        json_path=f"{DATA_DIR}/read_emails.json",
        store_path="vector_stores/read",
        source="read"
    )

    # ------------------------------------------------
    # 3. READ + REPLIED EMAILS
    # ------------------------------------------------

    create_vector_store(
        json_path=f"{DATA_DIR}/read_and_replied_emails.json",
        store_path="vector_stores/read_and_replied",
        source="read_and_replied"
    )

    print("\n" + "=" * 70)
    print("ALL VECTOR STORES CREATED")
    print("=" * 70)


if __name__ == "__main__":
    main()