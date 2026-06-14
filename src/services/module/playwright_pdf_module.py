import logging
from pathlib import Path
from typing import Any

import fitz
from playwright.sync_api import sync_playwright

from src.exceptions.convert_exception import ConvertPdfError


PLAYWRIGHT_TIMEOUT = 3000000

logger = logging.getLogger(__name__)


class PlaywrightPDFGenerator:
    def __init__(
        self,
        ws_endpoint: str | None = None,
        watermark_domain: str | None = None,
        watermark_text: str | None = None,
    ):
        self.ws_endpoint = ws_endpoint
        self.watermark_domain = watermark_domain
        self.watermark_text = watermark_text

    def _add_domain_watermark_domain(self, pdf_bytes: bytes) -> bytes | Any:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        font_size = 10
        font_name = "helv"

        if self.watermark_text:
            display_text = f"{self.watermark_text}: {self.watermark_domain}"
        else:
            display_text = f"{self.watermark_domain}"

        for i, page in enumerate(doc):
            page_num = i + 1

            if page_num == 1 or page_num % 50 == 0:
                rect = page.rect

                text_width = fitz.get_text_length(
                    display_text, fontname=font_name, fontsize=font_size
                )

                x = rect.width / 2 - text_width / 2
                y = rect.height - 20
                point = fitz.Point(x, y)

                page.insert_text(
                    point,
                    display_text,
                    fontsize=font_size,
                    fontname=font_name,
                    color=(0.5, 0.5, 0.5),
                )

                link_rect = fitz.Rect(x, y - font_size, x + text_width, y + 2)

                if self.watermark_domain and self.watermark_domain.startswith("http"):
                    url = self.watermark_domain
                else:
                    url = f"https://{self.watermark_domain}"

                page.insert_link({"kind": fitz.LINK_URI, "from": link_rect, "uri": url})

        return doc.write()

    def generate_pdf_bytes(self, html_content: str) -> bytes:
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
            raw_pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                margin={
                    "top": "20px",
                    "right": "20px",
                    "bottom": "40px",
                    "left": "20px",
                },
            )

            browser.close()

            if self.watermark_domain:
                final_pdf_bytes = self._add_domain_watermark_domain(raw_pdf_bytes)
            else:
                final_pdf_bytes = raw_pdf_bytes

            return final_pdf_bytes

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
