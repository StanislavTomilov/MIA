from langflow.custom import Component
from langflow.io import Output
from langflow.schema import Data

from ._recorder_singleton import get_recorder

class StopMeetingRecording(Component):
    display_name = "Stop Meeting Recording"
    description = "Остановить запись полной встречи и вернуть путь к WAV."
    icon = "square"
    name = "StopMeetingRecording"

    inputs = []

    outputs = [
        Output(name="stopped", display_name="Stopped", method="build_stopped"),
    ]

    def build_stopped(self) -> Data:
        rec = get_recorder()
        file_path = rec.stop_main_recording()
        self.status = f"Saved: {file_path}"
        return Data(data={"file_path": file_path})
