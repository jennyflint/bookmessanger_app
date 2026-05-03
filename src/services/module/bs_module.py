import json
from typing import Any

from bs4 import BeautifulSoup


class BsModule:
    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, "html.parser")

    def inject_json_to_script(self, tag_id: str, data: dict[str, Any]) -> bool:
        script_tag = self.soup.find("script", id=tag_id)

        if script_tag:
            json_string = json.dumps(data, ensure_ascii=False, indent=2)
            script_tag.string = json_string
            return True

        return False

    def update_title(self, new_title: str) -> bool:
        title_tag = self.soup.title

        if title_tag:
            title_tag.string = new_title
            return True

        return False

    def get_html(self) -> str:
        return self.soup.prettify()
