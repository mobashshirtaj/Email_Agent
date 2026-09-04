from unread_emails import (
    process_unread_emails
)

from read_not_replied import (
    process_read_not_replied
)

from replied_emails import (
    process_replied_emails
)

from emails_with_images import (
    process_emails_with_images
)


# ============================================================
# Main
# ============================================================

def main():

    print(
        "\n"
        "====================================================\n"
        "          GMAIL EMAIL PDF PROCESSOR\n"
        "====================================================\n"
    )

    try:

        # ----------------------------------------------------
        # 1. Unread emails
        # ----------------------------------------------------

        process_unread_emails()

        # ----------------------------------------------------
        # 2. Read but not replied
        # ----------------------------------------------------

        process_read_not_replied()

        # ----------------------------------------------------
        # 3. Read and replied
        # ----------------------------------------------------

        process_replied_emails()

        # ----------------------------------------------------
        # 4. Emails containing images
        # ----------------------------------------------------

        process_emails_with_images()

        # ----------------------------------------------------
        # Finished
        # ----------------------------------------------------

        print(
            "\n"
            "====================================================\n"
            "       ALL PROCESSING COMPLETED SUCCESSFULLY\n"
            "====================================================\n"
        )

    except KeyboardInterrupt:

        print(
            "\n\nProcess stopped by user."
        )

    except Exception as exc:

        print(
            "\n"
            "===================================================="
        )

        print(
            "ERROR"
        )

        print(
            "===================================================="
        )

        print(
            f"{type(exc).__name__}: {exc}"
        )


if __name__ == "__main__":
    main()