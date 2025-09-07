import pydantic
from pptx_rag_quizzer.presentation_model import Presentation

class RAG_quizzer(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    name: str
    presentation: Presentation
    collection_id: str
