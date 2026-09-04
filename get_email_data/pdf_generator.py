import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Image,
)
from reportlab.pdfgen import canvas


# ============================================================
# PDF Writer
# ============================================================

class PDFWriter:

    def __init__(
        self,
        output_file,
        title,
        include_images=False,
        include_replies=False
    ):

        self.output_file = output_file
        self.title = title
        self.include_images = include_images
        self.include_replies = include_replies

        self.canvas = canvas.Canvas(
            output_file,
            pagesize=A4
        )

        self.width, self.height = A4

        self.margin = 45

        self.current_y = (
            self.height - 50
        )

        self.styles = (
            getSampleStyleSheet()
        )

        self.label_style = (
            self.styles["BodyText"]
        )

        self.label_style.fontName = (
            "Helvetica-Bold"
        )

        self.label_style.fontSize = 9
        self.label_style.leading = 12

        self.body_style = (
            self.styles["BodyText"]
        )

        self.body_style.fontName = (
            "Helvetica"
        )

        self.body_style.fontSize = 9
        self.body_style.leading = 13

        self.title_style = (
            self.styles["Heading1"]
        )

        self.title_style.fontSize = 16
        self.title_style.leading = 20

        self.email_heading_style = (
            self.styles["Heading2"]
        )

        self.email_heading_style.fontSize = 12
        self.email_heading_style.leading = 15

        self._write_title()


    # ========================================================
    # Title
    # ========================================================

    def _write_title(self):

        paragraph = Paragraph(
            self.title,
            self.title_style
        )

        _, height = paragraph.wrap(
            self.width - 2 * self.margin,
            self.height
        )

        paragraph.drawOn(
            self.canvas,
            self.margin,
            self.current_y - height
        )

        self.current_y -= (
            height + 25
        )


    # ========================================================
    # New Page
    # ========================================================

    def new_page(self):

        self.canvas.showPage()

        self.current_y = (
            self.height - 50
        )


    # ========================================================
    # Check Space
    # ========================================================

    def ensure_space(
        self,
        required_height=50
    ):

        if (
            self.current_y
            - required_height
            < self.margin
        ):

            self.new_page()


    # ========================================================
    # Write Paragraph
    # ========================================================

    def write_text(
        self,
        text,
        style
    ):

        if text is None:
            text = ""

        # Escape characters that ReportLab
        # interprets as markup.

        import html

        text = html.escape(
            str(text)
        )

        text = text.replace(
            "\n",
            "<br/>"
        )

        paragraph = Paragraph(
            text,
            style
        )

        available_width = (
            self.width
            - 2 * self.margin
        )

        _, height = paragraph.wrap(
            available_width,
            self.height
        )

        self.ensure_space(
            height + 10
        )

        paragraph.drawOn(
            self.canvas,
            self.margin,
            self.current_y - height
        )

        self.current_y -= (
            height + 8
        )


    # ========================================================
    # Add Email
    # ========================================================

    def add_email(
        self,
        email_data
    ):

        self.ensure_space(
            100
        )


        # ----------------------------------------------------
        # Email heading
        # ----------------------------------------------------

        self.write_text(
            "EMAIL",
            self.email_heading_style
        )


        # ----------------------------------------------------
        # Only requested fields
        # ----------------------------------------------------

        self.write_text(
            f"From: {email_data.get('sender', '')}",
            self.label_style
        )

        self.write_text(
            f"Subject: {email_data.get('subject', '')}",
            self.label_style
        )

        self.write_text(
            f"Date: {email_data.get('date', '')}",
            self.label_style
        )


        self.write_text(
            "Content:",
            self.label_style
        )

        self.write_text(
            email_data.get(
                "body",
                "No readable content found."
            ),
            self.body_style
        )


        # ----------------------------------------------------
        # Images
        # ----------------------------------------------------

        if self.include_images:

            images = email_data.get(
                "images",
                []
            )

            if images:

                self.write_text(
                    "Images:",
                    self.label_style
                )

                for image_path in images:

                    if not os.path.exists(
                        image_path
                    ):
                        continue

                    try:

                        image = Image(
                            image_path
                        )

                        max_width = (
                            self.width
                            - 2 * self.margin
                        )

                        max_height = 300

                        scale = min(
                            max_width / image.imageWidth,
                            max_height / image.imageHeight,
                            1
                        )

                        image.drawWidth = (
                            image.imageWidth
                            * scale
                        )

                        image.drawHeight = (
                            image.imageHeight
                            * scale
                        )

                        self.ensure_space(
                            image.drawHeight + 20
                        )

                        image.drawOn(
                            self.canvas,
                            self.margin,
                            self.current_y
                            - image.drawHeight
                        )

                        self.current_y -= (
                            image.drawHeight + 20
                        )

                    except Exception:

                        pass


        # ----------------------------------------------------
        # Reply
        # ----------------------------------------------------

        if self.include_replies:

            reply = email_data.get(
                "reply"
            )

            if reply:

                self.ensure_space(
                    100
                )

                self.write_text(
                    "MY REPLY",
                    self.email_heading_style
                )

                self.write_text(
                    f"From: {reply.get('sender', '')}",
                    self.label_style
                )

                self.write_text(
                    f"Subject: {reply.get('subject', '')}",
                    self.label_style
                )

                self.write_text(
                    f"Date: {reply.get('date', '')}",
                    self.label_style
                )

                self.write_text(
                    "Content:",
                    self.label_style
                )

                self.write_text(
                    reply.get(
                        "body",
                        "No readable content found."
                    ),
                    self.body_style
                )


        # ----------------------------------------------------
        # Separator
        # ----------------------------------------------------

        self.canvas.line(
            self.margin,
            self.current_y,
            self.width - self.margin,
            self.current_y
        )

        self.current_y -= 20


    # ========================================================
    # Close
    # ========================================================

    def close(self):

        self.canvas.save()

        print(
            f"PDF created: {self.output_file}"
        )


# ============================================================
# Compatibility Function
# ============================================================

def create_pdf(
    emails,
    output_file,
    title,
    include_images=False,
    include_replies=False
):

    writer = PDFWriter(
        output_file,
        title,
        include_images=include_images,
        include_replies=include_replies
    )

    for email_data in emails:

        writer.add_email(
            email_data
        )

    writer.close()