"""
Initialize demo data for API configuration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.config import APIProvider, APIModel
from app.core.database import Base
from cryptography.fernet import Fernet
import json

# Database setup
DATABASE_URL = "sqlite:///./data/articles.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables exist
Base.metadata.create_all(bind=engine)

def create_demo_providers():
    """Create demo API providers."""
    db = SessionLocal()
    
    try:
        # Create encryption key for demo
        key = Fernet.generate_key()
        cipher = Fernet(key)
        
        # Demo providers
        providers = [
            {
                "name": "openai-gpt4",
                "display_name": "OpenAI GPT-4",
                "description": "OpenAI GPT-4 API服务，用于高质量文本生成和优化",
                "provider_type": "ai",
                "api_key": cipher.encrypt("sk-demo-key-1234567890".encode()).decode(),
                "api_url": "https://api.openai.com/v1",
                "api_version": "v1",
                "is_enabled": True,
                "is_default": True,
                "weight": 3,
                "max_requests_per_minute": 60,
                "max_requests_per_hour": 1000,
                "max_concurrent_requests": 5,
                "cost_per_1k_tokens_input": 0.03,
                "cost_per_1k_tokens_output": 0.06,
                "monthly_budget": 100.0,
                "success_rate": 98.5,
                "average_response_time": 1.2,
                "total_requests": 1250,
                "failed_requests": 18
            },
            {
                "name": "anthropic-claude",
                "display_name": "Anthropic Claude",
                "description": "Anthropic Claude API服务，擅长长文本处理和分析",
                "provider_type": "ai",
                "api_key": cipher.encrypt("sk-ant-demo-key-abcdef".encode()).decode(),
                "api_url": "https://api.anthropic.com",
                "api_version": "2023-06-01",
                "is_enabled": True,
                "is_default": False,
                "weight": 2,
                "max_requests_per_minute": 50,
                "max_requests_per_hour": 800,
                "max_concurrent_requests": 3,
                "cost_per_1k_tokens_input": 0.008,
                "cost_per_1k_tokens_output": 0.024,
                "monthly_budget": 80.0,
                "success_rate": 97.2,
                "average_response_time": 1.8,
                "total_requests": 890,
                "failed_requests": 25
            },
            {
                "name": "google-gemini",
                "display_name": "Google Gemini Pro",
                "description": "Google Gemini Pro API服务，支持多模态内容处理",
                "provider_type": "ai",
                "api_key": cipher.encrypt("AIzaSy-demo-key-xyz123".encode()).decode(),
                "api_url": "https://generativelanguage.googleapis.com/v1",
                "api_version": "v1",
                "is_enabled": False,
                "is_default": False,
                "weight": 1,
                "max_requests_per_minute": 40,
                "max_requests_per_hour": 600,
                "max_concurrent_requests": 2,
                "cost_per_1k_tokens_input": 0.0005,
                "cost_per_1k_tokens_output": 0.0015,
                "monthly_budget": 50.0,
                "success_rate": 95.8,
                "average_response_time": 2.1,
                "total_requests": 456,
                "failed_requests": 19
            },
            {
                "name": "zhuque-detection",
                "display_name": "朱雀AI检测",
                "description": "朱雀AI内容检测服务，用于检测AI生成内容",
                "provider_type": "detection",
                "api_key": cipher.encrypt("zhuque-demo-key-456".encode()).decode(),
                "api_url": "https://matrix.tencent.com/ai-detect",
                "is_enabled": True,
                "is_default": True,
                "weight": 1,
                "max_requests_per_minute": 20,
                "max_requests_per_hour": 200,
                "max_concurrent_requests": 1,
                "success_rate": 92.3,
                "average_response_time": 3.5,
                "total_requests": 234,
                "failed_requests": 18
            },
            {
                "name": "toutiao-publish",
                "display_name": "今日头条发布",
                "description": "今日头条内容发布服务",
                "provider_type": "publish",
                "api_key": cipher.encrypt("toutiao-demo-key-789".encode()).decode(),
                "api_url": "https://open.toutiao.com/api",
                "is_enabled": True,
                "is_default": True,
                "weight": 1,
                "max_requests_per_minute": 10,
                "max_requests_per_hour": 100,
                "max_concurrent_requests": 1,
                "success_rate": 89.7,
                "average_response_time": 2.8,
                "total_requests": 156,
                "failed_requests": 16
            }
        ]
        
        # Check if providers already exist
        try:
            existing_count = db.query(APIProvider).count()
            if existing_count > 0:
                print(f"Demo providers already exist ({existing_count} providers found)")
                return
        except Exception as e:
            print(f"Error checking existing providers: {e}")
            # Continue anyway
        
        # Create providers
        for provider_data in providers:
            provider = APIProvider(**provider_data)
            db.add(provider)
        
        db.commit()
        print(f"Created {len(providers)} demo providers successfully!")
        
        # Create some demo models for AI providers
        create_demo_models(db)
        
    except Exception as e:
        db.rollback()
        print(f"Error creating demo providers: {e}")
    finally:
        db.close()

def create_demo_models(db):
    """Create demo API models."""
    try:
        # Get AI providers
        ai_providers = db.query(APIProvider).filter(
            APIProvider.provider_type == "ai"
        ).all()
        
        models_data = []
        
        for provider in ai_providers:
            if "openai" in provider.name:
                models_data.extend([
                    {
                        "provider_id": provider.id,
                        "model_name": "gpt-4",
                        "display_name": "GPT-4",
                        "model_type": "text",
                        "max_tokens": 8192,
                        "temperature": 0.7,
                        "use_cases": json.dumps(["translation", "optimization", "summarization"])
                    },
                    {
                        "provider_id": provider.id,
                        "model_name": "gpt-4-turbo",
                        "display_name": "GPT-4 Turbo",
                        "model_type": "text",
                        "max_tokens": 128000,
                        "temperature": 0.7,
                        "use_cases": json.dumps(["translation", "optimization", "long_text"])
                    }
                ])
            elif "claude" in provider.name:
                models_data.extend([
                    {
                        "provider_id": provider.id,
                        "model_name": "claude-3-haiku-20240307",
                        "display_name": "Claude 3 Haiku",
                        "model_type": "text",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "use_cases": json.dumps(["translation", "optimization"])
                    },
                    {
                        "provider_id": provider.id,
                        "model_name": "claude-3-sonnet-20240229",
                        "display_name": "Claude 3 Sonnet",
                        "model_type": "text",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "use_cases": json.dumps(["translation", "optimization", "analysis"])
                    }
                ])
            elif "gemini" in provider.name:
                models_data.append({
                    "provider_id": provider.id,
                    "model_name": "gemini-pro",
                    "display_name": "Gemini Pro",
                    "model_type": "text",
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "use_cases": json.dumps(["translation", "optimization"])
                })
        
        # Create models
        for model_data in models_data:
            model = APIModel(**model_data)
            db.add(model)
        
        db.commit()
        print(f"Created {len(models_data)} demo models successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating demo models: {e}")

if __name__ == "__main__":
    print("Initializing demo data for API configuration...")
    create_demo_providers()
    print("Demo data initialization completed!")
