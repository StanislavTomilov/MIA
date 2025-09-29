from langflow.custom import Component
from langflow.io import Output
from langflow.schema import Data

from ._recorder_singleton import get_recorder

class StartQuestionRecording(Component):
    display_name = "Start Question Recording"
    description = "Старт короткой записи для режима вопроса."
    icon = "circle-dot"
    name = "StartQuestionRecording"

    inputs = []

    outputs = [
        Output(name="started", display_name="Started", method="build_started"),
    ]

    def build_started(self) -> Data:
        rec = get_recorder()
        rec.start_question_recording()
        self.status = "Question recording started"
        return Data(data={"ok": True})
