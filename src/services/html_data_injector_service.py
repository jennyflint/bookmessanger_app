from typing import Any

from src.exceptions.html_data_injector_exception import HtmlTagNotFoundError
from src.services.module.bs_module import BsModule


class HtmlDataInjectorService:
    def __init__(
        self, html_content: str, json_data: dict[str, Any], new_title: str = ""
    ):
        self.html_module = BsModule(html_content)
        self.json_data = json_data
        self.new_title = new_title

    def inject_json_to_script(self, tag_id: str, data: dict[str, Any]) -> bool:
        return self.html_module.inject_json_to_script(tag_id, data)

    def update_title(self, new_title: str) -> bool:
        return self.html_module.update_title(new_title)

    def get_html(self) -> str:
        return self.html_module.get_html()

    def main(self) -> str:
        if not self.inject_json_to_script("json-data", self.json_data):
            err_msg = "JSON data script tag not found"
            raise HtmlTagNotFoundError(err_msg)

        if self.new_title and not self.update_title(self.new_title):
            err_msg = "Title tag not found"
            raise HtmlTagNotFoundError(err_msg)
        return self.get_html()
