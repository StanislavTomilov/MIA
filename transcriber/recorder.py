import sounddevice as sd
import numpy as np
import soundfile as sf
import os
from datetime import datetime


def record_audio(duration_sec=10, sys_device=None, output_dir="audio"):
    if sys_device is None:
        raise ValueError("Нужно указать ID system-устройства (sys_device)")

    os.makedirs(output_dir, exist_ok=True)

    samplerate = 44100
    channels = 2
    print(f"🔴 Старт записи system-аудио на {duration_sec} сек")

    audio_data = sd.rec(
        int(duration_sec * samplerate),
        samplerate=samplerate,
        channels=channels,
        dtype='float32',
        device=sys_device
    )

    sd.wait()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(output_dir, f"meeting_{timestamp}.wav")

    sf.write(filename, audio_data, samplerate)

    print(f"✅ Запись завершена. Файл сохранён: {filename}")


# Версия для нескольких выходов

# import sounddevice as sd
# import soundfile as sf
# import numpy as np
# from datetime import datetime
# import os
# from utils.config import AUDIO_DIR, SAMPLE_RATE
#
# def record_audio(duration_sec=10, mic_device=None, sys_device=None):
#     os.makedirs(AUDIO_DIR, exist_ok=True)
#     timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#
#     mic_file = os.path.join(AUDIO_DIR, f"mic_{timestamp}.wav")
#     sys_file = os.path.join(AUDIO_DIR, f"sys_{timestamp}.wav")
#     mix_file = os.path.join(AUDIO_DIR, f"mix_{timestamp}.wav")
#
#     print(f"🎙️  Старт записи микрофона и системного звука на {duration_sec} сек")
#
#     mic_buffer = []
#     sys_buffer = []
#     total_frames = int(SAMPLE_RATE * duration_sec)
#     block_size = 1024
#
#     with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, device=mic_device, dtype='int16') as mic_stream, \
#          sd.InputStream(samplerate=SAMPLE_RATE, channels=1, device=sys_device, dtype='int16') as sys_stream:
#
#         for _ in range(0, total_frames, block_size):
#             mic_data, _ = mic_stream.read(block_size)
#             sys_data, _ = sys_stream.read(block_size)
#
#             mic_buffer.append(mic_data)
#             sys_buffer.append(sys_data)
#
#     mic_audio = np.concatenate(mic_buffer)
#     sys_audio = np.concatenate(sys_buffer)
#
#     # Сохраняем отдельно
#     sf.write(mic_file, mic_audio, SAMPLE_RATE)
#     sf.write(sys_file, sys_audio, SAMPLE_RATE)
#
#     # Смешиваем
#     mixed = mic_audio.astype(np.int32) + sys_audio.astype(np.int32)
#     mixed = np.clip(mixed, -32768, 32767).astype('int16')
#     sf.write(mix_file, mixed, SAMPLE_RATE)
#
#     print(f"✅ Запись завершена\n  🎤 Микрофон: {mic_file}\n  🎧 Система: {sys_file}\n  🎚️ Смешанный: {mix_file}")