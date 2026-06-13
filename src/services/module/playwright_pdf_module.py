import logging
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

from src.exceptions.convert_exception import ConvertPdfError


PLAYWRIGHT_TIMEOUT = 3000000

logger = logging.getLogger(__name__)


class PlaywrightPDFGenerator:
    def __init__(self, ws_endpoint: str | None = None):
        self.ws_endpoint = ws_endpoint

    def generate_pdf_bytes(self, html_content: str) -> Any:
        with sync_playwright() as p:
            if self.ws_endpoint:
                ws_url = self.ws_endpoint
                if "timeout=" not in ws_url:
                    separator = "&" if "?" in ws_url else "?"
                    ws_url = f"{ws_url}{separator}timeout={PLAYWRIGHT_TIMEOUT}"

                browser = p.chromium.connect_over_cdp(
                    ws_url, timeout=PLAYWRIGHT_TIMEOUT
                )
            else:
                browser = p.chromium.launch(headless=True)

            context = browser.new_context()
            page = context.new_page()

            page.set_default_timeout(PLAYWRIGHT_TIMEOUT)
            page.set_default_navigation_timeout(PLAYWRIGHT_TIMEOUT)

            page.set_content(html_content, wait_until="load")

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
            err_msg = f"Error saving PDF to file {file_path}"
            logger.exception(err_msg)
            raise ConvertPdfError(err_msg) from e
        else:
            return True
