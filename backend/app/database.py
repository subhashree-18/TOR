"""
Unified MongoDB Connection Manager
Provides centralized database connection with fallback logic and error handling
"""

import os
import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure

logger = logging.getLogger(__name__)


class MongoConnectionError(Exception):
    """Raised when MongoDB connection cannot be established"""
    pass


class MongoDBManager:
    """Singleton MongoDB connection manager with fallback and error handling"""
    
    _instance: Optional['MongoDBManager'] = None
    _client: Optional[MongoClient] = None
    _db = None
    
    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @staticmethod
    def get_mongo_urls() -> list:
        """
        Get list of MongoDB URLs to try in order of preference
        
        Returns:
            List of MongoDB connection URLs
        """
        urls = []
        
        # 1. Environment variable (highest priority)
        env_url = os.getenv("MONGO_URL")
        if env_url:
            urls.append(env_url)
            logger.info(f"Using MONGO_URL from environment: {env_url}")
        
        # 2. Local development URLs
        urls.extend([
            "mongodb://localhost:27017/torunveil",
            "mongodb://127.0.0.1:27017/torunveil",
        ])
        
        # 3. Docker Compose service discovery
        urls.extend([
            "mongodb://mongo:27017/torunveil",
            "mongodb://mongo-service:27017/torunveil",
        ])
        
        # 4. Kubernetes service discovery
        urls.extend([
            "mongodb://mongodb:27017/torunveil",
            "mongodb://mongodb.default.svc.cluster.local:27017/torunveil",
        ])
        
        return urls
    
    @staticmethod
    def _test_connection(client: MongoClient, timeout_ms: int = 5000) -> bool:
        """
        Test if a MongoDB client can connect
        
        Args:
            client: MongoClient instance
            timeout_ms: Timeout in milliseconds
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Ping the server
            client.admin.command('ping')
            return True
        except (ServerSelectionTimeoutError, Exception) as e:
            logger.debug(f"MongoDB connection test failed: {e}")
            return False
    
    def connect(self) -> 'MongoClient':
        """
        Establish MongoDB connection with fallback logic
        
        Returns:
            MongoClient instance
            
        Raises:
            MongoConnectionError: If all connection attempts fail
        """
        if self._client is not None:
            return self._client
        
        urls = self.get_mongo_urls()
        last_error = None
        
        for url in urls:
            try:
                logger.info(f"Attempting MongoDB connection to: {url}")
                
                client = MongoClient(
                    url,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    retryWrites=True,
                )
                
                # Test the connection
                if self._test_connection(client):
                    logger.info(f"✅ Successfully connected to MongoDB: {url}")
                    self._client = client
                    return client
                else:
                    logger.warning(f"❌ Connection test failed for: {url}")
                    client.close()
                    
            except Exception as e:
                last_error = e
                logger.debug(f"❌ Failed to connect to {url}: {type(e).__name__}: {e}")
                continue
        
        # All attempts failed
        error_msg = (
            f"Cannot connect to MongoDB. Tried {len(urls)} URL(s): "
            f"{', '.join(urls)}. Last error: {last_error}"
        )
        logger.error(error_msg)
        raise MongoConnectionError(error_msg)
    
    def get_db(self):
        """
        Get MongoDB database instance
        
        Returns:
            MongoDB database object
            
        Raises:
            MongoConnectionError: If connection fails
        """
        if self._db is None:
            client = self.connect()
            self._db = client["torunveil"]
            logger.info("✅ Database 'torunveil' ready")
        
        return self._db
    
    def get_client(self) -> MongoClient:
        """
        Get MongoDB client instance
        
        Returns:
            MongoClient instance
            
        Raises:
            MongoConnectionError: If connection fails
        """
        if self._client is None:
            self.connect()
        
        return self._client
    
    def close(self):
        """Close MongoDB connection"""
        if self._client is not None:
            try:
                self._client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {e}")
            finally:
                self._client = None
                self._db = None
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# Global manager instance
_db_manager = MongoDBManager()


def get_db():
    """
    Get MongoDB database instance (recommended way to use)
    
    Returns:
        MongoDB database object
        
    Raises:
        MongoConnectionError: If connection fails
    """
    return _db_manager.get_db()


def get_client() -> MongoClient:
    """
    Get MongoDB client instance
    
    Returns:
        MongoClient instance
        
    Raises:
        MongoConnectionError: If connection fails
    """
    return _db_manager.get_client()


def close_connection():
    """Close database connection"""
    _db_manager.close()
