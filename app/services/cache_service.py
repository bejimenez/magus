"""
Cache Service for Name Generator API

This module provides a caching abstraction that can use either:
1. In-memory caching (default, good for development/small deployments)
2. Redis caching (for production/distributed deployments)
3. No caching (for testing)

The service is designed to be non-breaking - if Redis fails or isn't configured,
it automatically falls back to in-memory caching.
"""

import json
import time
import hashlib
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
from collections import OrderedDict
from threading import Lock

logger = logging.getLogger(__name__)


class CacheBackend:
    """Base class for cache backends."""
    
    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        raise NotImplementedError
    
    async def clear_all(self) -> bool:
        raise NotImplementedError
    
    async def ping(self) -> bool:
        raise NotImplementedError


class InMemoryCache(CacheBackend):
    """
    Simple in-memory cache using Python dict.
    Good for development and single-instance deployments.
    Includes LRU (Least Recently Used) eviction when size limit is reached.
    """
    
    def __init__(self, max_size: int = 1000):
        self.cache: OrderedDict = OrderedDict()
        self.expiry: Dict[str, float] = {}
        self.max_size = max_size
        self.lock = Lock()
        self.hits = 0
        self.misses = 0
        logger.info(f"Initialized in-memory cache with max_size={max_size}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        with self.lock:
            # Check if key exists and hasn't expired
            if key in self.cache:
                expiry_time = self.expiry.get(key, float('inf'))
                if time.time() < expiry_time:
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    self.hits += 1
                    logger.debug(f"Cache hit: {key}")
                    return self.cache[key]
                else:
                    # Expired, remove it
                    del self.cache[key]
                    del self.expiry[key]
                    logger.debug(f"Cache expired: {key}")
            
            self.misses += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set a value in cache with TTL (time to live) in seconds."""
        try:
            with self.lock:
                # Evict oldest if at capacity
                if len(self.cache) >= self.max_size and key not in self.cache:
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    if oldest_key in self.expiry:
                        del self.expiry[oldest_key]
                    logger.debug(f"Evicted oldest key: {oldest_key}")
                
                # Store the value
                self.cache[key] = value
                self.cache.move_to_end(key)  # Mark as most recently used
                
                # Set expiry time
                if ttl > 0:
                    self.expiry[key] = time.time() + ttl
                
                logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
                return True
                
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.expiry:
                    del self.expiry[key]
                logger.debug(f"Cache deleted: {key}")
                return True
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cached data."""
        with self.lock:
            self.cache.clear()
            self.expiry.clear()
            self.hits = 0
            self.misses = 0
            logger.info("In-memory cache cleared")
            return True
    
    async def ping(self) -> bool:
        """Check if cache is available."""
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "type": "in-memory",
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": round(hit_rate, 2),
                "total_requests": total_requests
            }


class RedisCache(CacheBackend):
    """
    Redis cache backend for production deployments.
    Provides distributed caching across multiple application instances.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", key_prefix: str = "namegen:"):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection."""
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info(f"Initialized Redis cache at {self.redis_url}")
        except ImportError:
            logger.warning("Redis package not installed. Install with: pip install redis")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key for namespace isolation."""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis."""
        try:
            redis_key = self._make_key(key)
            value = await self.redis_client.get(redis_key)
            
            if value:
                # Deserialize JSON data
                logger.debug(f"Redis cache hit: {key}")
                return json.loads(value)
            
            logger.debug(f"Redis cache miss: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set a value in Redis with TTL."""
        try:
            redis_key = self._make_key(key)
            # Serialize to JSON
            json_value = json.dumps(value)
            
            if ttl > 0:
                await self.redis_client.setex(redis_key, ttl, json_value)
            else:
                await self.redis_client.set(redis_key, json_value)
            
            logger.debug(f"Redis cache set: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        try:
            redis_key = self._make_key(key)
            result = await self.redis_client.delete(redis_key)
            logger.debug(f"Redis cache deleted: {key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cached data with our prefix."""
        try:
            # Find all keys with our prefix
            pattern = f"{self.key_prefix}*"
            cursor = 0
            
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor, match=pattern, count=100
                )
                if keys:
                    await self.redis_client.delete(*keys)
                if cursor == 0:
                    break
            
            logger.info("Redis cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def ping(self) -> bool:
        """Check if Redis is available."""
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()


class NoOpCache(CacheBackend):
    """No-operation cache for testing or when caching is disabled."""
    
    async def get(self, key: str) -> Optional[Any]:
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        return True
    
    async def delete(self, key: str) -> bool:
        return True
    
    async def clear_all(self) -> bool:
        return True
    
    async def ping(self) -> bool:
        return True


class CacheService:
    """
    Main cache service that manages the backend and provides utility methods.
    This is what your application interacts with.
    """
    
    def __init__(self, settings):
        """
        Initialize cache service based on settings.
        
        Args:
            settings: Application settings object with cache configuration
        """
        self.settings = settings
        self.backend: Optional[CacheBackend] = None
        self.stats = {"hits": 0, "misses": 0}
        
    async def initialize(self):
        """Initialize the cache backend based on configuration."""
        try:
            if self.settings.cache_disabled:
                logger.info("Cache disabled by configuration")
                self.backend = NoOpCache()
                
            elif self.settings.use_redis:
                logger.info("Attempting to use Redis cache")
                try:
                    self.backend = RedisCache(
                        redis_url=self.settings.redis_url,
                        key_prefix=self.settings.redis_key_prefix
                    )
                    # Test connection
                    if await self.backend.ping():
                        logger.info("✓ Redis cache connected successfully")
                    else:
                        raise Exception("Redis ping failed")
                        
                except Exception as e:
                    logger.warning(f"Redis unavailable, falling back to in-memory cache: {e}")
                    self.backend = InMemoryCache(max_size=self.settings.cache_max_size)
            else:
                logger.info("Using in-memory cache")
                self.backend = InMemoryCache(max_size=self.settings.cache_max_size)
                
        except Exception as e:
            logger.error(f"Cache initialization failed, using no-op cache: {e}")
            self.backend = NoOpCache()
    
    def generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        Generate a consistent cache key from parameters.
        
        Args:
            prefix: Key prefix (e.g., "names", "culture")
            **kwargs: Parameters to include in the key
            
        Returns:
            Cache key string
        """
        # Sort parameters for consistent keys
        params = sorted(kwargs.items())
        param_str = "_".join(f"{k}:{v}" for k, v in params if v is not None)
        
        # For long parameter strings, use a hash
        if len(param_str) > 50:
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            return f"{prefix}_{param_hash}"
        
        return f"{prefix}_{param_str}" if param_str else prefix
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if not self.backend:
            return None
        
        value = await self.backend.get(key)
        if value is not None:
            self.stats["hits"] += 1
        else:
            self.stats["misses"] += 1
        
        return value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache."""
        if not self.backend:
            return False
        
        if ttl is None:
            ttl = self.settings.cache_ttl
        
        return await self.backend.set(key, value, ttl)
    
    async def get_or_generate(self, key: str, generator_func, ttl: Optional[int] = None):
        """
        Get from cache or generate if not found.
        
        Args:
            key: Cache key
            generator_func: Async function to generate value if not cached
            ttl: Time to live in seconds
            
        Returns:
            Cached or generated value
        """
        # Try to get from cache
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Generate new value
        value = await generator_func()
        
        # Store in cache
        await self.set(key, value, ttl)
        
        return value
    
    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if not self.backend:
            return False
        
        return await self.backend.delete(key)
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.
        Note: Only works efficiently with Redis.
        
        Args:
            pattern: Key pattern (e.g., "names_*")
            
        Returns:
            Number of keys deleted
        """
        if isinstance(self.backend, RedisCache):
            # Redis supports pattern matching
            count = 0
            cursor = 0
            while True:
                cursor, keys = await self.backend.redis_client.scan(
                    cursor, match=f"{self.backend.key_prefix}{pattern}", count=100
                )
                if keys:
                    await self.backend.redis_client.delete(*keys)
                    count += len(keys)
                if cursor == 0:
                    break
            return count
            
        elif isinstance(self.backend, InMemoryCache):
            # In-memory: iterate and match
            count = 0
            with self.backend.lock:
                keys_to_delete = [
                    k for k in self.backend.cache.keys()
                    if self._pattern_match(k, pattern)
                ]
                for key in keys_to_delete:
                    del self.backend.cache[key]
                    if key in self.backend.expiry:
                        del self.backend.expiry[key]
                    count += 1
            return count
        
        return 0
    
    def _pattern_match(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for in-memory cache."""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)
    
    async def clear_all(self) -> bool:
        """Clear all cached data."""
        if not self.backend:
            return False
        
        return await self.backend.clear_all()
    
    async def ping(self) -> bool:
        """Check if cache is available."""
        if not self.backend:
            return False
        
        return await self.backend.ping()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        base_stats = {
            "backend": self.backend.__class__.__name__ if self.backend else "None",
            "app_hits": self.stats["hits"],
            "app_misses": self.stats["misses"]
        }
        
        # Add backend-specific stats
        if isinstance(self.backend, InMemoryCache):
            base_stats.update(self.backend.get_stats())
        elif isinstance(self.backend, RedisCache):
            try:
                info = await self.backend.redis_client.info()
                base_stats.update({
                    "type": "redis",
                    "redis_version": info.get("redis_version"),
                    "used_memory_human": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients")
                })
            except Exception:
                pass
        
        return base_stats
    
    async def close(self):
        """Close cache connections."""
        if isinstance(self.backend, RedisCache):
            await self.backend.close()
    
    # ========================================================================
    # NAME GENERATOR SPECIFIC METHODS
    # ========================================================================
    
    async def cache_generated_names(
        self,
        culture: str,
        gender: Optional[str],
        names: List[Dict],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache a list of generated names.
        
        Args:
            culture: Culture code
            gender: Gender or None
            names: List of name dictionaries
            ttl: Time to live
            
        Returns:
            Success boolean
        """
        key = self.generate_cache_key(
            "names",
            culture=culture,
            gender=gender,
            count=len(names)
        )
        return await self.set(key, names, ttl)
    
    async def get_cached_names(
        self,
        culture: str,
        gender: Optional[str],
        count: int
    ) -> Optional[List[Dict]]:
        """
        Get cached names for specific parameters.
        
        Args:
            culture: Culture code
            gender: Gender or None
            count: Number of names requested
            
        Returns:
            List of cached names or None
        """
        key = self.generate_cache_key(
            "names",
            culture=culture,
            gender=gender,
            count=count
        )
        return await self.get(key)
    
    async def invalidate_culture_cache(self, culture: str):
        """
        Invalidate all cached data for a specific culture.
        Useful when culture definition is updated.
        
        Args:
            culture: Culture code to invalidate
        """
        pattern = f"names_culture:{culture}_*"
        deleted = await self.clear_pattern(pattern)
        logger.info(f"Invalidated {deleted} cache entries for culture: {culture}")


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_cache_service(settings) -> CacheService:
    """
    Factory function to create a cache service instance.
    
    Args:
        settings: Application settings object
        
    Returns:
        Configured CacheService instance
    """
    return CacheService(settings)