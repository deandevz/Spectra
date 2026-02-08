import re
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str, **variables: str) -> tuple[str, str]:
    """Load an XML prompt file and return (system_message, user_message).

    Variables in the prompt are replaced using {variable_name} syntax.
    """
    path = _PROMPTS_DIR / f"{name}.xml"
    content = path.read_text(encoding="utf-8")

    for key, value in variables.items():
        content = content.replace(f"{{{key}}}", str(value))

    system = _extract_tag(content, "system")
    user = _extract_tag(content, "user")

    return system, user


def _extract_tag(content: str, tag: str) -> str:
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return ""
    return match.group(1).strip()
