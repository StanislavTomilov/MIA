import subprocess
import os
import sys
import threading
import time
from datetime import datetime

def ensure_virtual_cable_and_loopback():
    # 1. Проверяем VirtualCable
    sinks = subprocess.check_output(['pactl', 'list', 'sinks', 'short']).decode()
    if "VirtualCable" not in sinks:
        print("[AudioSetup] VirtualCable не найден, создаём...")
        subprocess.run([
            'pactl', 'load-module', 'module-null-sink',
            'sink_name=VirtualCable',
            'sink_properties=device.description=VirtualCable',
            'rate=48000', 'format=s16le', 'channels=1'
        ], check=True)

        subprocess.run([
            'pactl', 'load-module', 'module-loopback',
            f'source=alsa_output.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__hw_sofhdadsp__sink.monitor',
            'sink=VirtualCable',
            'latency_msec=50',
            'rate=48000',
            'channels=2',
            'use_mmap=false'
        ], check=True)

        subprocess.run([
            'pactl', 'load-module', 'module-loopback',
            f'source=source=alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__hw_sofhdadsp_6__source',
            'sink=VirtualCable',
            'latency_msec=50',
            'rate=48000',
            'channels=2',
            'use_mmap=false'
        ], check=True)

    else:
        print("[AudioSetup] VirtualCable уже создан.")

    # 2. Проверяем наличие нужного loopback (по названию source и sink)
    modules = subprocess.check_output(['pactl', 'list', 'modules', 'short']).decode()
    need_source = 'alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__hw_sofhdadsp_6__source'
    loopback_found = False
    for line in modules.splitlines():
        if 'module-loopback' in line and 'sink=VirtualCable' in line and f'source={need_source}' in line:
            loopback_found = True
            break
    if not loopback_found:
        print("[AudioSetup] Loopback не найден, создаём...")
        subprocess.run([
            'pactl', 'load-module', 'module-loopback',
            f'source={need_source}',
            'sink=VirtualCable',
            'latency_msec=50',
            'rate=48000',
            'channels=2',
            'use_mmap=false'
        ], check=True)
    else:
        print("[AudioSetup] Loopback уже создан.")

# Пример вызова:
ensure_virtual_cable_and_loopback()


AUDIO_DIR = "audio"
AUDIO_DIR_MEET = os.path.join(AUDIO_DIR, "meetings")
AUDIO_DIR_QUEST = os.path.join(AUDIO_DIR, "questions")
os.makedirs(AUDIO_DIR_MEET, exist_ok=True)
os.makedirs(AUDIO_DIR_QUEST, exist_ok=True)

def _generate_filename(prefix):
    """
    prefix: 'meeting' | 'question'
    """
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if prefix == "meeting":
        folder = AUDIO_DIR_MEET
    elif prefix == "question":
        folder = AUDIO_DIR_QUEST
    else:
        folder = AUDIO_DIR
    return f"{folder}/{prefix}_{ts}_{sys.platform}.wav"

class Recorder:
    def __init__(self,
                 monitor_name="VirtualCable.monitor",
                 samplerate=48000,
                 channels=1):
        self.monitor_name = monitor_name
        self.samplerate = samplerate
        self.channels = channels
        self.main_proc = None
        self.main_sox = None
        self.main_filename = None
        self.question_proc = None
        self.question_sox = None
        self.question_filename = None

        os.makedirs(AUDIO_DIR, exist_ok=True)
        print(f"[Recorder] monitor={monitor_name}, samplerate={samplerate}, channels={channels}")

    def _start_parec_recording(self, filename, duration_sec=None):
        parec_cmd = [
            "parec", "-d", self.monitor_name,
            f"--rate={self.samplerate}",
            "--format=s16le",
            f"--channels={self.channels}",
            "--latency-msec=1"
        ]
        sox_cmd = [
            "sox", "-t", "raw", f"-r{self.samplerate}",
            "-e", "signed-integer", "-b", "16",
            f"-c{self.channels}", "-", filename
        ]
        parec_proc = subprocess.Popen(parec_cmd, stdout=subprocess.PIPE)
        sox_proc = subprocess.Popen(sox_cmd, stdin=parec_proc.stdout)

        if duration_sec is not None:
            def stop_after_delay():
                time.sleep(duration_sec)
                try:
                    parec_proc.terminate()
                    sox_proc.terminate()
                except Exception as e:
                    print("[Recorder] Ошибка при остановке процесса:", e)
            threading.Thread(target=stop_after_delay, daemon=True).start()

        return parec_proc, sox_proc

    def start_main_recording(self):
        filename = _generate_filename("meeting")
        print(f"[Recorder] ▶️ Запись встречи: {filename}")
        self.main_proc, self.main_sox = self._start_parec_recording(filename)
        self.main_filename = filename

    def stop_main_recording(self):
        print("[Recorder] ⏹ Останавливаю основную запись...")
        if self.main_proc:
            self.main_proc.terminate()
        if self.main_sox:
            self.main_sox.terminate()
            self.main_sox.wait()
        print(f"[Recorder] ✅ Основная запись завершена, файл сохранён: {self.main_filename}")
        return self.main_filename

    def start_question_recording(self):
        filename = _generate_filename("question")
        print(f"[Recorder] 🔴 Запись вопроса: {filename}")
        self.question_proc, self.question_sox = self._start_parec_recording(filename)
        self.question_filename = filename

    def stop_question_recording(self):
        print("[Recorder] 🔵 Останавливаю запись вопроса...")
        if self.question_proc:
            self.question_proc.terminate()
        if self.question_sox:
            self.question_sox.terminate()
            self.question_sox.wait()
        print(f"[Recorder] ✅ Запись вопроса завершена, файл сохранён: {self.question_filename}")
        return self.question_filename

    @classmethod
    def create_auto(cls, monitor_name=None, samplerate=48000, channels=1):
        # Готовим PulseAudio окружение (если используешь эту функцию)
        ensure_virtual_cable_and_loopback()
        if monitor_name is None:
            monitor_name = "VirtualCable.monitor"
        return cls(monitor_name=monitor_name, samplerate=samplerate, channels=channels)
