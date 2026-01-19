"""
Application Configuration
=========================
Centralized configuration management for the Calorie Vision Tracker.
"""

import os
from dataclasses import dataclass
from typing import Optional
import streamlit as st

@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # App Info
    APP_NAME: str = "Calorie Vision Tracker"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Track your calories using AI-powered food image analysis"
    
    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    
    # Anthropic Claude Configuration
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 1024
    
    # SendGrid (for email digests)
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = ""
    
    # Image Settings
    MAX_IMAGE_SIZE_MB: int = 10
    SUPPORTED_IMAGE_TYPES: tuple = ("jpg", "jpeg", "png", "webp", "heic")
    
    # Default User Settings
    DEFAULT_CALORIE_TARGET: int = 2000
    DEFAULT_TIMEZONE: str = "America/Bogota"
    
    # Analytics Settings
    ROLLING_AVERAGE_DAYS: int = 7
    WEEKLY_DIGEST_DAY: int = 0  # Monday


def get_config() -> AppConfig:
    """
    Load configuration from Streamlit secrets or environment variables.
    Priority: Streamlit secrets > Environment variables > Defaults
    """
    config = AppConfig()
    
    # Try Streamlit secrets first, then env vars
    def get_secret(key: str, default: str = "") -> str:
        try:
            return st.secrets.get(key, os.getenv(key, default))
        except:
            return os.getenv(key, default)
    
    # Load secrets
    config.SUPABASE_URL = get_secret("SUPABASE_URL")
    config.SUPABASE_ANON_KEY = get_secret("SUPABASE_ANON_KEY")
    config.ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
    config.SENDGRID_API_KEY = get_secret("SENDGRID_API_KEY")
    config.SENDGRID_FROM_EMAIL = get_secret("SENDGRID_FROM_EMAIL")
    
    return config


def validate_config(config: AppConfig) -> tuple[bool, list[str]]:
    """
    Validate that required configuration is present.
    Returns (is_valid, list of missing keys).
    """
    missing = []
    
    if not config.SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not config.SUPABASE_ANON_KEY:
        missing.append("SUPABASE_ANON_KEY")
    if not config.ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    
    return len(missing) == 0, missing


# TDEE Calculator Constants
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,       # Little or no exercise
    "light": 1.375,         # Light exercise 1-3 days/week
    "moderate": 1.55,       # Moderate exercise 3-5 days/week
    "active": 1.725,        # Hard exercise 6-7 days/week
    "very_active": 1.9      # Very hard exercise, physical job
}

# Meal Type Configuration
MEAL_TYPES = {
    1: {"name": "Breakfast", "icon": "🌅", "start": "06:00", "end": "10:00"},
    2: {"name": "Morning Snack", "icon": "🍎", "start": "10:00", "end": "12:00"},
    3: {"name": "Lunch", "icon": "☀️", "start": "12:00", "end": "14:00"},
    4: {"name": "Afternoon Snack", "icon": "🍪", "start": "14:00", "end": "17:00"},
    5: {"name": "Dinner", "icon": "🌙", "start": "17:00", "end": "21:00"},
    6: {"name": "Evening Snack", "icon": "🌃", "start": "21:00", "end": "23:59"},
    7: {"name": "Beverage", "icon": "🥤", "start": "00:00", "end": "23:59"}
}


# Claude Vision Prompt Template
FOOD_ANALYSIS_PROMPT = """Analyze this food image and provide nutritional estimates.

IMPORTANT GUIDELINES:
1. Identify all visible food items and beverages
2. Estimate portion sizes based on visual cues (plate size, utensils, etc.)
3. Provide calorie and macro estimates based on typical nutritional data
4. Be conservative with estimates when uncertain
5. Consider that this may be a home-cooked meal

Please respond in the following JSON format ONLY (no other text):
{
    "food_items": [
        {
            "name": "Item name",
            "portion": "Estimated portion (e.g., '1 cup', '200g', '1 medium')",
            "calories": 000
        }
    ],
    "total_calories": 000,
    "macros": {
        "protein_g": 00.0,
        "carbs_g": 00.0,
        "fat_g": 00.0,
        "fiber_g": 00.0,
        "sugar_g": 00.0
    },
    "confidence": 0.0,
    "description": "Brief description of the meal",
    "notes": "Any relevant notes about the estimation"
}

CONFIDENCE SCORING:
- 0.9-1.0: Clear image, common foods, visible portions
- 0.7-0.9: Good image, some estimation required
- 0.5-0.7: Unclear portions or unfamiliar foods
- Below 0.5: Significant uncertainty

Respond with ONLY the JSON, no markdown formatting or backticks."""


# Quick Add Calorie Presets
QUICK_ADD_PRESETS = [
    {"name": "Glass of Water", "calories": 0, "icon": "💧"},
    {"name": "Black Coffee", "calories": 5, "icon": "☕"},
    {"name": "Coffee with Milk", "calories": 50, "icon": "☕"},
    {"name": "Apple", "calories": 95, "icon": "🍎"},
    {"name": "Banana", "calories": 105, "icon": "🍌"},
    {"name": "Small Snack (100 cal)", "calories": 100, "icon": "🍪"},
    {"name": "Medium Snack (200 cal)", "calories": 200, "icon": "🍿"},
    {"name": "Large Snack (300 cal)", "calories": 300, "icon": "🥨"},
]
