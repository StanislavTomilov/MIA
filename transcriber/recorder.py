import os
from datetime import datetime
import subprocess
import soundfile as sf

import sounddevice as sd

def _find_device_id_by_name(name_parts):
    """
    name_parts: список подстрок для поиска (например, ["VirtualCable", "pulse", "default"])
    Ищет по output и input девайсам.
    """
    devices = sd.query_devices()
    # Сначала ищем по output
    for name in name_parts:
        for idx, dev in enumerate(devices):
            if name.lower() in dev['name'].lower() and dev['max_output_channels'] > 0:
                print(f"✅ Найдено output-устройство: {dev['name']} (id={idx})")
                return idx
    # Затем ищем по input
    for name in name_parts:
        for idx, dev in enumerate(devices):
            if name.lower() in dev['name'].lower() and dev['max_input_channels'] > 0:
                print(f"✅ Найдено input-устройство: {dev['name']} (id={idx})")
                return idx
    # Не найдено — печатаем всё, что есть
    print(f"❌ Не найдено подходящего устройства из списка: {name_parts}")
    print("\nВсе устройства:")
    for idx, dev in enumerate(devices):
        print(f"ID: {idx:2d} | name: {dev['name']} | in: {dev['max_input_channels']} | out: {dev['max_output_channels']}")
    raise RuntimeError(
        f"\nНе найдено ни одного устройства из {name_parts}. Проверь настройку виртуального кабеля и PulseAudio/PipeWire!"
    )


def record_audio_windows(duration_sec=10, output_dir="audio"):
    """
    Запись аудио с VB-Cable, Stereo Mix или другого виртуального устройства на Windows.
    """
    os.makedirs(output_dir, exist_ok=True)
    for virtual_name in ["VB-Cable", "Stereo Mix"]:
        try:
            device_id = _find_device_id_by_name(virtual_name)
            break
        except RuntimeError:
            device_id = None
    if device_id is None:
        raise RuntimeError(
            "Не найден VB-Cable или Stereo Mix! Подключи virtual audio device и выставь его как системный выход."
        )

    samplerate = 48000
    channels = 1
    dtype = 'int16'

    print(f"🔴 Запись аудио Windows: {duration_sec} сек, device id {device_id}")
    audio = sd.rec(
        int(duration_sec * samplerate),
        samplerate=samplerate,
        channels=channels,
        dtype=dtype,
        device=device_id
    )
    sd.wait()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(output_dir, f"meeting_{timestamp}_win.wav")
    sf.write(filename, audio, samplerate, subtype='PCM_16')
    print(f"✅ Файл сохранён: {filename}")
    return filename

def record_audio_linux(duration_sec=10, output_dir="audio"):
    """
    Запись system audio на Linux с помощью parec + sox (максимальное качество, как в терминале).
    Требует настроенного VirtualCable с monitor-источником.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(output_dir, f"meeting_{timestamp}_linux.wav")

    # Команды для записи — ровно как ты писал в терминале!
    parec_cmd = [
        "parec", "-d", "VirtualCable.monitor",
        "--rate=48000", "--format=s16le", "--channels=1", "--latency-msec=1"
    ]

    sox_cmd = [
        "sox", "-t", "raw", "-r", "48000", "-e", "signed-integer", "-b", "16", "-c", "1", "-V1", "-", filename
    ]

    print(f"🔴 Запись через parec + sox ({duration_sec} сек)...")

    # Запускаем parec → sox через пайп
    parec_proc = subprocess.Popen(parec_cmd, stdout=subprocess.PIPE)
    sox_proc = subprocess.Popen(sox_cmd, stdin=parec_proc.stdout)

    try:
        sox_proc.wait(timeout=duration_sec)
    except subprocess.TimeoutExpired:
        print("⏹ Останавливаем запись (timeout)...")
        parec_proc.terminate()
        sox_proc.terminate()

    abs_path = os.path.abspath(filename)
    print(f"✅ Файл сохранён: {abs_path}")
    return filename

def record_audio_mac(duration_sec=10, output_dir="audio"):
    """
    Запись аудио с BlackHole или другого virtual audio device на Mac.
    """
    os.makedirs(output_dir, exist_ok=True)
    device_id = _find_device_id_by_name("BlackHole")
    samplerate = 48000
    channels = 1
    dtype = 'int16'

    print(f"🔴 Запись аудио MacOS: {duration_sec} сек, device id {device_id}")
    audio = sd.rec(
        int(duration_sec * samplerate),
        samplerate=samplerate,
        channels=channels,
        dtype=dtype,
        device=device_id
    )
    sd.wait()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(output_dir, f"meeting_{timestamp}_mac.wav")
    sf.write(filename, audio, samplerate, subtype='PCM_16')
    print(f"✅ Файл сохранён: {filename}")
    return filename
