"""Streamlit utilities for caching and performance"""
import functools
from datetime import datetime, timedelta
from typing import Any, Callable, Optional
import logging

import streamlit as st

logger = logging.getLogger(__name__)


class CacheManager:
    """Manage cache with TTL support"""
    
    def __init__(self):
        self._cache: dict[str, tuple[Any, datetime]] = {}
    
    def get(self, key: str, ttl_seconds: int = 300) -> Optional[Any]:
        """Get cached value if not expired"""
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        
        if datetime.now() - timestamp > timedelta(seconds=ttl_seconds):
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set cached value with current timestamp"""
        self._cache[key] = (value, datetime.now())
    
    def clear(self, key: Optional[str] = None) -> None:
        """Clear cache entry or entire cache"""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self._cache),
            "keys": list(self._cache.keys()),
        }


# Global cache manager
_cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Get global cache manager"""
    return _cache_manager


def cached_api_call(
    ttl_seconds: int = 300,
    key_prefix: str = ""
) -> Callable:
    """
    Decorator to cache API call results
    
    Args:
        ttl_seconds: Time to live for cache in seconds
        key_prefix: Optional prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            cached = _cache_manager.get(cache_key, ttl_seconds)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Cache result
            _cache_manager.set(cache_key, result)
            logger.debug(f"Cache set: {cache_key}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            cached = _cache_manager.get(cache_key, ttl_seconds)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            _cache_manager.set(cache_key, result)
            logger.debug(f"Cache set: {cache_key}")
            
            return result
        
        # Return appropriate wrapper
        if hasattr(func, "__self__"):
            return async_wrapper
        else:
            return sync_wrapper if not hasattr(func, "__await__") else async_wrapper
        
        return sync_wrapper
    
    return decorator


def clear_cache():
    """Clear all cached data"""
    _cache_manager.clear()
    logger.info("Cache cleared")


class PerformanceMonitor:
    """Monitor performance metrics"""
    
    def __init__(self):
        self._metrics: dict[str, list[float]] = {}
    
    def record(self, metric_name: str, value: float) -> None:
        """Record a metric"""
        if metric_name not in self._metrics:
            self._metrics[metric_name] = []
        
        self._metrics[metric_name].append(value)
    
    def get_average(self, metric_name: str) -> float:
        """Get average value for metric"""
        if metric_name not in self._metrics or not self._metrics[metric_name]:
            return 0.0
        
        return sum(self._metrics[metric_name]) / len(self._metrics[metric_name])
    
    def get_stats(self, metric_name: str) -> dict[str, float]:
        """Get statistics for metric"""
        if metric_name not in self._metrics or not self._metrics[metric_name]:
            return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
        
        values = self._metrics[metric_name]
        
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }
    
    def clear(self) -> None:
        """Clear all metrics"""
        self._metrics.clear()


# Global performance monitor
_perf_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor"""
    return _perf_monitor
