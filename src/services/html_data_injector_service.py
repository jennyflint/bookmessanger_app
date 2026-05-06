from src.settings.settings import book_settings
from src.template_manager import TemplateManager


class HtmlDataInjectorService:
    def __init__(self, template: str, json_data: str, new_title: str = ""):
        self.template = template
        self.json_data = json_data
        self.new_title = new_title

        self.template_manager = TemplateManager(
            book_settings.storage / book_settings.storage_html_template
        )

    def main(self) -> str:
        format_data = {
            "json_data": self.json_data,
            "title": self.new_title,
        }

        return self.template_manager.render(self.template + ".html", **format_data)
