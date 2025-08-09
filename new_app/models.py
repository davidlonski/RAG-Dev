import pydantic
from pptx_rag_quizzer.presentation_model import Presentation

class RAG_quizzer(pydantic.BaseModel):
    id: str
    name: str
    presentation: Presentation
    collection_id: str
