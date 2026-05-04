"""
Smart Cache Manager for Patent Automation System

This module provides intelligent caching for:
- Downloaded patent data from external APIs
- Academic paper data from arXiv
- Sentence transformer models and embeddings
- Vector analysis results

Features:
- Content-based caching with hash validation
- Cache health checks and corruption detection
- Size monitoring and automatic cleanup
- Incremental updates
- Cache invalidation strategies
"""

import os
import json
import hashlib
import pickle
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
import gzip
import sqlite3

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Represents a cached item with metadata"""
    key: str
    content_hash: str
    content_type: str  # 'patent_data', 'academic_paper', 'embedding', 'model'
    source: str  # 'lens', 'epo', 'arxiv', 'sentence_transformer'
    created_at: datetime
    last_accessed: datetime
    size_bytes: int
    metadata: Dict[str, Any]
    is_valid: bool = True

class SmartCacheManager:
    """Intelligent cache manager with health checks and size monitoring"""
    
    def __init__(self, cache_dir: str = "smart_cache", max_size_mb: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.db_path = self.cache_dir / "cache_metadata.db"
        
        # Create cache directory structure
        self._setup_cache_structure()
        
        # Initialize database
        self._init_database()
        
        # Cache settings
        self.enable_caching = True
        self.cache_ttl_hours = 24  # Cache entries expire after 24 hours
        self.health_check_interval_hours = 6
        
    def _setup_cache_structure(self):
        """Create cache directory structure"""
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different content types
        (self.cache_dir / "patent_data").mkdir(exist_ok=True)
        (self.cache_dir / "academic_papers").mkdir(exist_ok=True)
        (self.cache_dir / "embeddings").mkdir(exist_ok=True)
        (self.cache_dir / "models").mkdir(exist_ok=True)
        (self.cache_dir / "vector_results").mkdir(exist_ok=True)
        
    def _init_database(self):
        """Initialize SQLite database for cache metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                content_type TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                metadata TEXT NOT NULL,
                is_valid INTEGER NOT NULL DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def _get_content_hash(self, content: Any) -> str:
        """Generate hash for content"""
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, sort_keys=True)
        else:
            content_str = str(content)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _get_cache_path(self, content_type: str, key: str) -> Path:
        """Get file path for cached content"""
        return self.cache_dir / content_type / f"{key}.gz"
    
    def _compress_content(self, content: Any) -> bytes:
        """Compress content for storage"""
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, sort_keys=True)
        else:
            content_str = str(content)
        return gzip.compress(content_str.encode())
    
    def _decompress_content(self, compressed_data: bytes) -> Any:
        """Decompress content from storage"""
        content_str = gzip.decompress(compressed_data).decode()
        try:
            return json.loads(content_str)
        except json.JSONDecodeError:
            return content_str
    
    def get(self, key: str, content_type: str) -> Optional[Any]:
        """Retrieve cached content if valid"""
        if not self.enable_caching:
            return None
            
        try:
            # Check database for entry
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM cache_entries 
                WHERE key = ? AND content_type = ? AND is_valid = 1
            ''', (key, content_type))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            
            # Check if entry is expired
            created_at = datetime.fromisoformat(row[4])
            if datetime.now() - created_at > timedelta(hours=self.cache_ttl_hours):
                logger.info(f"Cache entry expired for {key}")
                self._invalidate_entry(key, content_type)
                conn.close()
                return None
            
            # Check if file exists
            cache_path = self._get_cache_path(content_type, key)
            if not cache_path.exists():
                logger.warning(f"Cache file missing for {key}")
                self._invalidate_entry(key, content_type)
                conn.close()
                return None
            
            # Load and validate content
            try:
                with open(cache_path, 'rb') as f:
                    compressed_data = f.read()
                
                content = self._decompress_content(compressed_data)
                
                # Update last accessed time
                cursor.execute('''
                    UPDATE cache_entries 
                    SET last_accessed = ? 
                    WHERE key = ? AND content_type = ?
                ''', (datetime.now().isoformat(), key, content_type))
                
                conn.commit()
                conn.close()
                
                logger.info(f"✅ Cache hit for {key} ({content_type})")
                return content
                
            except Exception as e:
                logger.error(f"Error loading cached content for {key}: {e}")
                self._invalidate_entry(key, content_type)
                conn.close()
                return None
                
        except Exception as e:
            logger.error(f"Error accessing cache for {key}: {e}")
            return None
    
    def set(self, key: str, content: Any, content_type: str, source: str, metadata: Dict[str, Any] = None) -> bool:
        """Store content in cache"""
        if not self.enable_caching:
            return False
            
        try:
            # Generate content hash
            content_hash = self._get_content_hash(content)
            
            # Compress content
            compressed_data = self._compress_content(content)
            size_bytes = len(compressed_data)
            
            # Check cache size and cleanup if needed
            if not self._ensure_cache_space(size_bytes):
                logger.warning(f"Insufficient cache space for {key}")
                return False
            
            # Store compressed content
            cache_path = self._get_cache_path(content_type, key)
            with open(cache_path, 'wb') as f:
                f.write(compressed_data)
            
            # Store metadata in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            metadata_str = json.dumps(metadata or {})
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries 
                (key, content_hash, content_type, source, created_at, last_accessed, size_bytes, metadata, is_valid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (key, content_hash, content_type, source, now, now, size_bytes, metadata_str))
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Cached {key} ({content_type}) - {size_bytes} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Error caching {key}: {e}")
            return False
    
    def _ensure_cache_space(self, required_bytes: int) -> bool:
        """Ensure sufficient cache space by cleaning up old entries"""
        current_size = self._get_cache_size()
        
        if current_size + required_bytes <= self.max_size_bytes:
            return True
        
        # Need to clean up
        logger.info(f"Cache cleanup needed: {current_size} + {required_bytes} > {self.max_size_bytes}")
        
        # Remove expired entries first
        self._cleanup_expired_entries()
        
        # If still not enough space, remove least recently used entries
        if self._get_cache_size() + required_bytes > self.max_size_bytes:
            self._cleanup_lru_entries(required_bytes)
        
        return self._get_cache_size() + required_bytes <= self.max_size_bytes
    
    def _get_cache_size(self) -> int:
        """Get total cache size in bytes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT SUM(size_bytes) FROM cache_entries WHERE is_valid = 1')
        result = cursor.fetchone()
        
        conn.close()
        return result[0] or 0
    
    def _cleanup_expired_entries(self):
        """Remove expired cache entries"""
        cutoff_time = datetime.now() - timedelta(hours=self.cache_ttl_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT key, content_type FROM cache_entries 
            WHERE created_at < ? AND is_valid = 1
        ''', (cutoff_time.isoformat(),))
        
        expired_entries = cursor.fetchall()
        
        for key, content_type in expired_entries:
            self._invalidate_entry(key, content_type)
        
        conn.close()
        
        if expired_entries:
            logger.info(f"🧹 Cleaned up {len(expired_entries)} expired cache entries")
    
    def _cleanup_lru_entries(self, required_bytes: int):
        """Remove least recently used entries to free space"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT key, content_type, size_bytes FROM cache_entries 
            WHERE is_valid = 1 
            ORDER BY last_accessed ASC
        ''')
        
        entries = cursor.fetchall()
        freed_bytes = 0
        
        for key, content_type, size_bytes in entries:
            if freed_bytes >= required_bytes:
                break
                
            self._invalidate_entry(key, content_type)
            freed_bytes += size_bytes
        
        conn.close()
        
        logger.info(f"🧹 Freed {freed_bytes} bytes by removing LRU entries")
    
    def _invalidate_entry(self, key: str, content_type: str):
        """Invalidate a cache entry"""
        try:
            # Remove file
            cache_path = self._get_cache_path(content_type, key)
            if cache_path.exists():
                cache_path.unlink()
            
            # Mark as invalid in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE cache_entries 
                SET is_valid = 0 
                WHERE key = ? AND content_type = ?
            ''', (key, content_type))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error invalidating cache entry {key}: {e}")
    
    def clear_cache(self, content_type: Optional[str] = None):
        """Clear cache (all or specific type)"""
        try:
            if content_type:
                # Clear specific content type
                type_dir = self.cache_dir / content_type
                if type_dir.exists():
                    shutil.rmtree(type_dir)
                    type_dir.mkdir(exist_ok=True)
                
                # Update database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE cache_entries 
                    SET is_valid = 0 
                    WHERE content_type = ?
                ''', (content_type,))
                conn.commit()
                conn.close()
                
                logger.info(f"🧹 Cleared {content_type} cache")
            else:
                # Clear all cache
                for subdir in self.cache_dir.iterdir():
                    if subdir.is_dir() and subdir.name != "__pycache__":
                        shutil.rmtree(subdir)
                        subdir.mkdir(exist_ok=True)
                
                # Clear database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('UPDATE cache_entries SET is_valid = 0')
                conn.commit()
                conn.close()
                
                logger.info("🧹 Cleared all cache")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total entries
            cursor.execute('SELECT COUNT(*) FROM cache_entries WHERE is_valid = 1')
            total_entries = cursor.fetchone()[0]
            
            # Total size
            cursor.execute('SELECT SUM(size_bytes) FROM cache_entries WHERE is_valid = 1')
            total_size = cursor.fetchone()[0] or 0
            
            # Entries by type
            cursor.execute('''
                SELECT content_type, COUNT(*), SUM(size_bytes) 
                FROM cache_entries 
                WHERE is_valid = 1 
                GROUP BY content_type
            ''')
            type_stats = {}
            for content_type, count, size in cursor.fetchall():
                type_stats[content_type] = {
                    'count': count,
                    'size_bytes': size or 0
                }
            
            # Oldest and newest entries
            cursor.execute('''
                SELECT MIN(created_at), MAX(created_at) 
                FROM cache_entries 
                WHERE is_valid = 1
            ''')
            oldest, newest = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_entries': total_entries,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'utilization_percent': (total_size / self.max_size_bytes) * 100 if self.max_size_bytes > 0 else 0,
                'type_stats': type_stats,
                'oldest_entry': oldest,
                'newest_entry': newest,
                'cache_enabled': self.enable_caching
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        try:
            stats = self.get_cache_stats()
            
            # Check for corruption
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT key, content_type FROM cache_entries 
                WHERE is_valid = 1
            ''')
            
            corrupted_entries = []
            for key, content_type in cursor.fetchall():
                cache_path = self._get_cache_path(content_type, key)
                if not cache_path.exists():
                    corrupted_entries.append((key, content_type))
            
            conn.close()
            
            # Fix corrupted entries
            for key, content_type in corrupted_entries:
                self._invalidate_entry(key, content_type)
            
            health_status = {
                'is_healthy': len(corrupted_entries) == 0,
                'corrupted_entries': len(corrupted_entries),
                'stats': stats,
                'last_check': datetime.now().isoformat()
            }
            
            if corrupted_entries:
                logger.warning(f"Found {len(corrupted_entries)} corrupted cache entries")
            else:
                logger.info("✅ Cache health check passed")
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error during cache health check: {e}")
            return {
                'is_healthy': False,
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def get_patent_cache_key(self, patent_id: str, search_terms: List[str]) -> str:
        """Generate cache key for patent search results"""
        search_str = "|".join(sorted(search_terms))
        return f"patent_{patent_id}_{hashlib.md5(search_str.encode()).hexdigest()}"
    
    def get_academic_cache_key(self, paper_id: str, search_terms: List[str]) -> str:
        """Generate cache key for academic paper search results"""
        search_str = "|".join(sorted(search_terms))
        return f"academic_{paper_id}_{hashlib.md5(search_str.encode()).hexdigest()}"
    
    def get_embedding_cache_key(self, text: str, model_name: str) -> str:
        """Generate cache key for embeddings"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"embedding_{model_name}_{text_hash}"

# Global cache manager instance
smart_cache = SmartCacheManager() 