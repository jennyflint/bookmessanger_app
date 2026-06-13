import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


logger = logging.getLogger(__name__)


class TemplateManager:
    def __init__(self, templates_dir: str | Path):
        self.templates_dir = str(Path(templates_dir).resolve())
        self._env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False,  # noqa: S701
        )

    def render(self, template_name: str, **kwargs: Any) -> str:
        try:
            template = self._env.get_template(template_name)
            return template.render(**kwargs)
        except TemplateNotFound as err:
            err_msg = f"Template '{template_name}' \
                not found in folder {self.templates_dir}"

            logger.exception(err_msg)
            raise FileNotFoundError(err_msg) from err
