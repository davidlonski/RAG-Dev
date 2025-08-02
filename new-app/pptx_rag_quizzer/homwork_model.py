from enum import Enum
from typing import List
import pydantic

class Question_type(Enum):
    text = "text"
    image = "image"

class Homework_item(pydantic.BaseModel):
    id: str
    type: Question_type
    collection_id: str
    context: str
    answer: str
    question: str


class Image_question(Homework_item):
    image_bytes: bytes
    extension: str

class Text_question(Homework_item):
    pass

class Homework(pydantic.BaseModel):
    id: str
    items: List[Homework_item]
    collection_id: str