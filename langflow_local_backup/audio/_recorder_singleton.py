# langflow/audio/_recorder_singleton.py
from typing import Optional
from transcriber.recorder import Recorder  # <-- импортируем твой готовый Recorder

_REC: Optional[Recorder] = None

def get_recorder(monitor_name: str = "VirtualCable.monitor", samplerate: int = 48000, channels: int = 1) -> Recorder:
    global _REC
    if _REC is None:
        _REC = Recorder.create_auto(monitor_name=monitor_name, samplerate=samplerate, channels=channels)
    return _REC
