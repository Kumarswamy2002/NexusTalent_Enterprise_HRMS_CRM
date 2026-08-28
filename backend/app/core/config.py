"""
NexusTalent / Elevate-HR Enterprise Platform
Core Configuration & Environment Settings
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "NexusTalent Enterprise HRMS & CRM"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = True
    
    # Security & Tokens
    SECRET_KEY: str = Field(default="nexustalent-enterprise-super-secret-key-2026-production-grade", env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Multi-tenancy & Database
    DATABASE_URL: str = Field(
        default=f"sqlite+aiosqlite:///{BASE_DIR}/nexustalent_enterprise.db",
        env="DATABASE_URL"
    )
    SYNC_DATABASE_URL: str = Field(
        default=f"sqlite:///{BASE_DIR}/nexustalent_enterprise.db",
        env="SYNC_DATABASE_URL"
    )
    DEFAULT_TENANT_ID: str = "tenant-enterprise-global"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Geofencing Defaults (Headquarters coordinates)
    HQ_LATITUDE: float = 37.7749
    HQ_LONGITUDE: float = -122.4194
    GEOFENCE_RADIUS_METERS: float = 200.0
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
