from langflow.custom import Component
from langflow.io import FileInput, StrInput, Output
from langflow.schema import Data
from transcriber.whisper import transcribe_file  # (path, language, model_size) -> str

class MIATranscribe(Component):
    display_name = "Transcriber"
    description  = "Транскрибация аудио Whisper (CUDA)"
    icon = "mic"
    name = "Transcriber"
    inputs = [
        FileInput(name="audio_path", display_name="Audio file"),
        StrInput(name="language", display_name="Language", value="ru"),
        StrInput(name="model_size", display_name="Whisper model", value="large-v3"),
    ]
    outputs = [Output(name="transcript", display_name="Transcript", method="run")]
    def run(self) -> Data:
        text = transcribe_file(self.audio_path, language=self.language, model_size=self.model_size)
        return Data(data={"text": text}, text=text)
