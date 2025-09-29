from langflow.custom import Component
from langflow.io import StrInput, IntInput, Output
from langflow.schema import Data

from ._recorder_singleton import get_recorder

class StartMeetingRecording(Component):
    display_name = "Start Meeting Recording"
    description = "Старт записи полной встречи (parec|sox через твой Recorder)."
    icon = "play"
    name = "StartMeetingRecording"

    inputs = [
        StrInput(name="monitor_name", display_name="Pulse monitor", value="VirtualCable.monitor"),
        IntInput(name="samplerate", display_name="Sample rate", value=48000),
        IntInput(name="channels", display_name="Channels", value=1),
    ]

    outputs = [
        Output(name="started", display_name="Started", method="build_started"),
    ]

    def build_started(self) -> Data:
        rec = get_recorder(self.monitor_name, self.samplerate, self.channels)
        rec.start_main_recording()
        self.status = f"Meeting recording started (monitor={self.monitor_name})"
        return Data(data={
            "monitor": self.monitor_name,
            "samplerate": self.samplerate,
            "channels": self.channels
        })
