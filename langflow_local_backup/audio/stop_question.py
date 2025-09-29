from langflow.custom import Component
from langflow.io import Output
from langflow.schema import Data

from ._recorder_singleton import get_recorder

class StopQuestionRecording(Component):
    display_name = "Stop Question Recording"
    description = "Останавливает запись вопроса и возвращает путь к WAV."
    icon = "stop-circle"
    name = "StopQuestionRecording"

    inputs = []

    outputs = [
        Output(name="stopped", display_name="Stopped", method="build_stopped"),
    ]

    def build_stopped(self) -> Data:
        rec = get_recorder()
        file_path = rec.stop_question_recording()
        self.status = f"Saved: {file_path}"
        return Data(data={"file_path": file_path})
