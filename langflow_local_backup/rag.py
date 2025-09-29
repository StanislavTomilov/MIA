from langflow.custom import Component
from langflow.io import StrInput, IntInput, Output
from langflow.schema import Data, Message
from rag.search import answer_with_context  # (query, k) -> obj{answer:str, docs:list}

class MIARAGSearch(Component):
    display_name = "MIA RAG Search"
    description  = "Поиск по базе встреч и ответ"
    icon = "search"
    name = "MIA_RAG_Search"
    inputs = [
        StrInput(name="query", display_name="Query"),
        IntInput(name="k", display_name="Top-K", value=5),
    ]
    outputs = [
        Output(name="answer", display_name="Answer", method="answer"),
        Output(name="hits",   display_name="Top Docs", method="hits", group_outputs=True),
    ]
    def answer(self) -> Message:
        res = answer_with_context(self.query, k=self.k)
        return Message(text=res.answer)
    def hits(self) -> Data:
        res = answer_with_context(self.query, k=self.k)
        rows = [{"score": d.score, "id": d.id, "path": d.path, "snippet": d.snippet} for d in res.docs]
        return Data(data={"rows": rows, "columns": list(rows[0].keys()) if rows else []})
