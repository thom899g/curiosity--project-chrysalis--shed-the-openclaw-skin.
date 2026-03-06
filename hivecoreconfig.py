"""
HiveCore Configuration Manager - Centralized configuration with environment awareness.
Architectural Rationale:
1. Singleton pattern prevents multiple config instances consuming memory
2. Environment variables with fallbacks ensure deployment flexibility
3. Type-hinted configuration enables IDE autocomplete and runtime validation
4. Lazy loading reduces startup memory footprint
"""

import os
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables from .env file if present
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    logging.warning("No .env file found, using system environment variables")

@dataclass(frozen=True)
class FirebaseConfig:
    """Firebase configuration with validation and type safety"""
    project_id: str = os.getenv("FIREBASE_PROJECT_ID", "hivecore-production")
    credentials_path: str = os.getenv("FIREBASE_CREDENTIALS", "firebase-credentials.json")
    firestore_collection: str = os.getenv("FIRESTORE_COLLECTION", "api_services")
    
    def validate(self) -> bool:
        """Validate Firebase configuration"""
        if not Path(self.credentials_path).exists():
            logging.error(f"Firebase credentials not found at {self.credentials_path}")
            return False
        return True

@dataclass(frozen=True)
class StripeConfig:
    """Stripe payment processing configuration"""
    secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    default_currency: str = os.getenv("STRIPE_CURRENCY", "usd")
    minimum_charge: float = float(os.getenv("STRIPE_MIN_CHARGE", "0.10"))
    
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured"""
        return bool(self.secret_key and len(self.secret_key) > 20)

@dataclass(frozen=True)
class APIConfig:
    """API service broker configuration"""
    service_discovery_interval: int = int(os.getenv("DISCOVERY_INTERVAL", "300"))
    max_concurrent_requests: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    enable_rate_limiting: bool = os.getenv("ENABLE_RATE_LIMIT", "true").lower() == "true"
    revenue_target: float = float(os.getenv("REVENUE_TARGET", "1.00"))

class HiveCoreConfig:
    """Singleton configuration manager"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize configuration with environment validation"""
        self.firebase = FirebaseConfig()
        self.stripe = StripeConfig()
        self.api = APIConfig()
        
        # Validate critical configurations
        if not self.firebase.validate():
            raise ValueError("Firebase configuration validation failed")
        
        if not self.stripe.is_configured():
            logging.warning("Stripe not fully configured - revenue generation disabled")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    @property
    def memory_budget_mb(self) -> int:
        """Get memory budget based on environment"""
        return int(os.getenv("MEMORY_BUDGET_MB", "100" if self.is_production else "50"))

# Global configuration instance
config = HiveCoreConfig()