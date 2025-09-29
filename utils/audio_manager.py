"""
Оптимизированный менеджер аудио
"""
import subprocess
import os
import sys
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from contextlib import contextmanager

from utils.config import get_config

logger = logging.getLogger(__name__)


class AudioSetupError(Exception):
    """Исключение для ошибок настройки аудио"""
    pass


class AudioRecordingError(Exception):
    """Исключение для ошибок записи"""
    pass


class AudioManager:
    """Оптимизированный менеджер аудио"""
    
    def __init__(self, config: dict):
        self.config = config
        self.monitor_name = config["virtual_cable_name"]
        self.samplerate = config["sample_rate"]
        self.channels = config["channels"]
        
        # Процессы записи
        self.main_proc: Optional[subprocess.Popen] = None
        self.main_sox: Optional[subprocess.Popen] = None
        self.main_filename: Optional[str] = None
        
        self.question_proc: Optional[subprocess.Popen] = None
        self.question_sox: Optional[subprocess.Popen] = None
        self.question_filename: Optional[str] = None
        
        # Директории
        self.audio_dir = Path(config["audio_dir"])
        self.meetings_dir = self.audio_dir / "meetings"
        self.questions_dir = self.audio_dir / "questions"
        
        # Создание директорий
        self.meetings_dir.mkdir(parents=True, exist_ok=True)
        self.questions_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"AudioManager initialized: monitor={self.monitor_name}, "
                   f"samplerate={self.samplerate}, channels={self.channels}")
    
    def setup_virtual_cable(self) -> None:
        """Настройка VirtualCable с улучшенной обработкой ошибок"""
        try:
            # Проверяем VirtualCable
            sinks = subprocess.check_output(['pactl', 'list', 'sinks', 'short'], 
                                          text=True, stderr=subprocess.PIPE)
            
            if "VirtualCable" not in sinks:
                logger.info("Creating VirtualCable...")
                self._create_virtual_cable()
            else:
                logger.info("VirtualCable already exists")
            
            # Проверяем loopback
            self._ensure_loopback_exists()
            
        except subprocess.CalledProcessError as e:
            raise AudioSetupError(f"Failed to setup audio: {e.stderr.decode()}")
        except FileNotFoundError:
            raise AudioSetupError("pactl not found. Please install PulseAudio")
    
    def _create_virtual_cable(self) -> None:
        """Создание VirtualCable"""
        # Создаем null sink
        subprocess.run([
            'pactl', 'load-module', 'module-null-sink',
            'sink_name=VirtualCable',
            'sink_properties=device.description=VirtualCable',
            f'rate={self.samplerate}', 'format=s16le', f'channels={self.channels}'
        ], check=True, capture_output=True, text=True)
        
        # Создаем loopback для системного аудио
        self._create_loopback("alsa_output.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__hw_sofhdadsp__sink.monitor")
        
        # Создаем loopback для микрофона
        self._create_loopback("alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__hw_sofhdadsp_6__source")
    
    def _create_loopback(self, source: str) -> None:
        """Создание loopback для указанного источника"""
        subprocess.run([
            'pactl', 'load-module', 'module-loopback',
            f'source={source}',
            'sink=VirtualCable',
            f'latency_msec={self.config["audio_latency_ms"]}',
            f'rate={self.samplerate}',
            'channels=2',
            'use_mmap=false'
        ], check=True, capture_output=True, text=True)
    
    def _ensure_loopback_exists(self) -> None:
        """Проверка и создание недостающего loopback"""
        modules = subprocess.check_output(['pactl', 'list', 'modules', 'short'], 
                                        text=True, stderr=subprocess.PIPE)
        
        need_source = 'alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__hw_sofhdadsp_6__source'
        loopback_found = any(
            'module-loopback' in line and 'sink=VirtualCable' in line and f'source={need_source}' in line
            for line in modules.splitlines()
        )
        
        if not loopback_found:
            logger.info("Creating missing loopback...")
            self._create_loopback(need_source)
        else:
            logger.info("Loopback already exists")
    
    def _generate_filename(self, prefix: str) -> str:
        """Генерация имени файла с временной меткой"""
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder = self.meetings_dir if prefix == "meeting" else self.questions_dir
        return str(folder / f"{prefix}_{ts}_{sys.platform}.wav")
    
    def _start_recording(self, filename: str, duration_sec: Optional[int] = None) -> Tuple[subprocess.Popen, subprocess.Popen]:
        """Запуск записи с улучшенной обработкой ошибок"""
        try:
            # Команда parec
            parec_cmd = [
                "parec", "-d", self.monitor_name,
                f"--rate={self.samplerate}",
                "--format=s16le",
                f"--channels={self.channels}",
                "--latency-msec=1"
            ]
            
            # Команда sox
            sox_cmd = [
                "sox", "-t", "raw", f"-r{self.samplerate}",
                "-e", "signed-integer", "-b", "16",
                f"-c{self.channels}", "-", filename
            ]
            
            # Запуск процессов
            parec_proc = subprocess.Popen(parec_cmd, stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE, text=True)
            sox_proc = subprocess.Popen(sox_cmd, stdin=parec_proc.stdout, 
                                      stderr=subprocess.PIPE, text=True)
            
            # Автоматическая остановка через duration_sec
            if duration_sec is not None:
                def stop_after_delay():
                    time.sleep(duration_sec)
                    self._terminate_processes(parec_proc, sox_proc)
                
                threading.Thread(target=stop_after_delay, daemon=True).start()
            
            return parec_proc, sox_proc
            
        except FileNotFoundError as e:
            raise AudioRecordingError(f"Required audio tool not found: {e}")
        except subprocess.SubprocessError as e:
            raise AudioRecordingError(f"Failed to start recording: {e}")
    
    def _terminate_processes(self, *processes) -> None:
        """Безопасное завершение процессов"""
        for proc in processes:
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                except Exception as e:
                    logger.warning(f"Error terminating process: {e}")
    
    def start_main_recording(self) -> str:
        """Запуск записи встречи"""
        filename = self._generate_filename("meeting")
        logger.info(f"Starting meeting recording: {filename}")
        
        self.main_proc, self.main_sox = self._start_recording(filename)
        self.main_filename = filename
        return filename
    
    def stop_main_recording(self) -> str:
        """Остановка записи встречи"""
        logger.info("Stopping main recording...")
        
        self._terminate_processes(self.main_proc, self.main_sox)
        
        if self.main_filename and Path(self.main_filename).exists():
            logger.info(f"Main recording completed: {self.main_filename}")
            return self.main_filename
        else:
            raise AudioRecordingError("Recording file not found")
    
    def start_question_recording(self) -> str:
        """Запуск записи вопроса"""
        filename = self._generate_filename("question")
        logger.info(f"Starting question recording: {filename}")
        
        self.question_proc, self.question_sox = self._start_recording(filename)
        self.question_filename = filename
        return filename
    
    def stop_question_recording(self) -> str:
        """Остановка записи вопроса"""
        logger.info("Stopping question recording...")
        
        self._terminate_processes(self.question_proc, self.question_sox)
        
        if self.question_filename and Path(self.question_filename).exists():
            logger.info(f"Question recording completed: {self.question_filename}")
            return self.question_filename
        else:
            raise AudioRecordingError("Question recording file not found")
    
    def cleanup(self) -> None:
        """Очистка ресурсов"""
        self._terminate_processes(
            self.main_proc, self.main_sox,
            self.question_proc, self.question_sox
        )


@contextmanager
def audio_manager_context(config: dict):
    """Контекстный менеджер для AudioManager"""
    manager = AudioManager(config)
    try:
        manager.setup_virtual_cable()
        yield manager
    finally:
        manager.cleanup()

