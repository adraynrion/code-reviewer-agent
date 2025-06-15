from pydantic import BaseModel, Field


class CodeReviewResponse(BaseModel):
    """Response model for the generated code review response."""

    line_number: int = Field(
        ..., description="The line number where the issue or suggestion applies"
    )

    code_diff: str = Field(
        ...,
        description="A properly formatted code suggestion using `diff` syntax (inside a Markdown fenced code block) showing how the developer should fix the issue",
    )

    comment: str = Field(
        ...,
        description="A clear and detailed explanation of what the issue is, why it matters, and how to fix it. Be educational and constructive.",
    )

    title: str = Field(
        ..., description="A short, descriptive title summarizing the feedback"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "line_number": 1,
                "code_diff": "```diff\n- # Ceci est un commentaire en français\n+ # This is a comment in English\n````\n",
                "comment": "We enforce the use of English in comments and documentation for this project.",
                "title": "Use English in comments and documentation",
            }
        }
    }

    def __repr__(self) -> str:
        return f"Line number: {self.line_number}\nCode diff: {self.code_diff}\nComment: {self.comment}\nTitle: {self.title}"
