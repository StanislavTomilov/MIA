from transcriber.recorder import record_audio

if __name__ == "__main__":
    # Укажи только system_device (например, VB-Cable или Stereo Mix)
    record_audio(duration_sec=10, sys_device=1)  # ← укажи ID своего system-устройства
