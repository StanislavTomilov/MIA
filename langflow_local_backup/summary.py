from langflow.custom import Component
from langflow.io import MessageTextInput, StrInput, Output
from langflow.schema import Message
from llms.tasks import summarize_transcript  # (text, style) -> str

class MIASummarize(Component):
    display_name = "MIA Summarize"
    description  = "Создать summary по транскрипту"
    icon = "file-text"
    name = "MIA_Summarize"
    inputs = [
        MessageTextInput(name="transcript", display_name="Transcript"),
        StrInput(name="style", display_name="Style", value="exec_summary"),
    ]
    outputs = [Output(name="summary", display_name="Summary", method="run")]
    def run(self) -> Message:
        text = summarize_transcript(self.transcript, style=self.style)
        return Message(text=text)
