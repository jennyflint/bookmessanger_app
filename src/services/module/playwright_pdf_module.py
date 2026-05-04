from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

from src.exceptions.convert_exception import ConvertPdfError


class PlaywrightPDFGenerator:
    def __init__(self, ws_endpoint: str | None = None):
        self.ws_endpoint = ws_endpoint

    def generate_pdf_bytes(self, html_content: str) -> Any:
        with sync_playwright() as p:
            if self.ws_endpoint:
                browser = p.chromium.connect_over_cdp(self.ws_endpoint)
            else:
                browser = p.chromium.launch(headless=True)

            context = browser.new_context()
            page = context.new_page()
            page.set_content(html_content, wait_until="networkidle")

            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                margin={
                    "top": "20px",
                    "right": "20px",
                    "bottom": "20px",
                    "left": "20px",
                },
            )

            browser.close()

            return pdf_bytes

    def save_pdf_to_file(self, html_content: str, file_path: str) -> bool:
        try:
            pdf_bytes = self.generate_pdf_bytes(html_content)
            target_path = Path(file_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(pdf_bytes)
        except Exception as e:
            raise ConvertPdfError(str(e)) from e
        else:
            return True
