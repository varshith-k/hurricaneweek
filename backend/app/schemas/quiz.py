from pydantic import BaseModel


class QuizQuestion(BaseModel):
    id: str
    question: str
    options: list[str]
    correct_index: int
    explanation: str
    source: str


class QuizResponse(BaseModel):
    title: str
    disclaimer: str
    questions: list[QuizQuestion]
