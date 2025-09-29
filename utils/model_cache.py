"""
Система кэширования моделей
"""
import logging
import threading
from typing import Dict, Any, Optional
from functools import lru_cache
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ModelCache:
    """Кэш для моделей с потокобезопасностью"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._loading: Dict[str, threading.Event] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Получить модель из кэша"""
        with self._lock:
            return self._cache.get(key)
    
    def set(self, key: str, model: Any) -> None:
        """Сохранить модель в кэш"""
        with self._lock:
            self._cache[key] = model
            logger.info(f"Model cached: {key}")
    
    def has(self, key: str) -> bool:
        """Проверить наличие модели в кэше"""
        with self._lock:
            return key in self._cache
    
    def clear(self) -> None:
        """Очистить кэш"""
        with self._lock:
            self._cache.clear()
            logger.info("Model cache cleared")
    
    def get_or_load(self, key: str, loader_func, *args, **kwargs) -> Any:
        """Получить модель из кэша или загрузить"""
        # Проверяем кэш
        if self.has(key):
            logger.info(f"Using cached model: {key}")
            return self.get(key)
        
        # Проверяем, не загружается ли уже
        with self._lock:
            if key in self._loading:
                loading_event = self._loading[key]
            else:
                loading_event = threading.Event()
                self._loading[key] = loading_event
        
        # Если уже загружается, ждем
        if loading_event.is_set():
            loading_event.wait()
            return self.get(key)
        
        # Загружаем модель
        try:
            logger.info(f"Loading model: {key}")
            model = loader_func(*args, **kwargs)
            self.set(key, model)
            return model
        finally:
            loading_event.set()
            with self._lock:
                self._loading.pop(key, None)


# Глобальный кэш моделей
model_cache = ModelCache()


# Декораторы для кэширования
def cached_model(key_func=None):
    """Декоратор для кэширования моделей"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Генерируем ключ кэша
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            return model_cache.get_or_load(cache_key, func, *args, **kwargs)
        return wrapper
    return decorator


# Специализированные функции кэширования
def get_asr_cache_key(model_size: str, device: str, compute_type: str) -> str:
    """Ключ кэша для ASR модели"""
    return f"asr_{model_size}_{device}_{compute_type}"


def get_embedder_cache_key(model_name: str, device: str) -> str:
    """Ключ кэша для эмбеддера"""
    return f"embedder_{model_name}_{device}"


@contextmanager
def model_cache_context():
    """Контекстный менеджер для работы с кэшем моделей"""
    try:
        yield model_cache
    finally:
        # Можно добавить логику очистки при выходе
        pass

