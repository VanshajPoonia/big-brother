"""Checks on what Qwen returns that need the issue for context."""

from bigbrother.schema import Issue, Symptom


def _squash(text: str) -> str:
    # Models copy the words but often drop Markdown marks like `code` and **bold**.
    return " ".join(text.replace("`", "").replace("*", "").split()).lower()


def symptom_is_quoted(issue: Issue, symptom: Symptom) -> bool:
    """The symptom has to come from the report itself, so the model can't invent one."""
    return _squash(symptom.quote) in _squash(issue.text)
