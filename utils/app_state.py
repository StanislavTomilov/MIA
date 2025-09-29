"""
Управление состоянием приложения
"""
from dataclasses import dataclass
from typing import Set, Optional
from pynput import keyboard as kb
import threading
from contextlib import contextmanager


@dataclass
class AppState:
    """Состояние приложения"""
    is_meeting_active: bool = False
    is_question_active: bool = False
    pressed_keys: Set = None
    
    def __post_init__(self):
        if self.pressed_keys is None:
            self.pressed_keys = set()


class StateManager:
    """Менеджер состояния приложения с потокобезопасностью"""
    
    def __init__(self):
        self._state = AppState()
        self._lock = threading.Lock()
    
    @contextmanager
    def state_context(self):
        """Контекстный менеджер для безопасного изменения состояния"""
        with self._lock:
            yield self._state
    
    def is_meeting_active(self) -> bool:
        with self._lock:
            return self._state.is_meeting_active
    
    def is_question_active(self) -> bool:
        with self._lock:
            return self._state.is_question_active
    
    def set_meeting_active(self, active: bool):
        with self._lock:
            self._state.is_meeting_active = active
    
    def set_question_active(self, active: bool):
        with self._lock:
            self._state.is_question_active = active
    
    def add_pressed_key(self, key):
        with self._lock:
            self._state.pressed_keys.add(key)
    
    def remove_pressed_key(self, key):
        with self._lock:
            self._state.pressed_keys.discard(key)
    
    def get_pressed_keys(self) -> Set:
        with self._lock:
            return self._state.pressed_keys.copy()
    
    def has_key_combination(self, ctrl_keys, char_keys) -> bool:
        """Проверяет наличие комбинации клавиш"""
        with self._lock:
            pressed = self._state.pressed_keys
            has_ctrl = any(ctrl in pressed for ctrl in ctrl_keys)
            has_char = any(hasattr(key, 'char') and key.char in char_keys for key in pressed)
            return has_ctrl and has_char


# Глобальный экземпляр менеджера состояния
state_manager = StateManager()

