"""
Utility Functions
=================
Helper functions for calculations, formatting, and data processing.
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math


# =============================================================================
# TDEE CALCULATOR
# =============================================================================

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,       # Little or no exercise, desk job
    "light": 1.375,         # Light exercise 1-3 days/week
    "moderate": 1.55,       # Moderate exercise 3-5 days/week
    "active": 1.725,        # Hard exercise 6-7 days/week
    "very_active": 1.9      # Very hard exercise, physical job, training 2x/day
}

ACTIVITY_DESCRIPTIONS = {
    "sedentary": "Little or no exercise, desk job",
    "light": "Light exercise 1-3 days/week",
    "moderate": "Moderate exercise 3-5 days/week",
    "active": "Hard exercise 6-7 days/week",
    "very_active": "Very hard exercise, physical job"
}


def calculate_bmr(
    weight_kg: float, 
    height_cm: float, 
    age_years: int, 
    gender: str
) -> float:
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.
    
    This is considered the most accurate formula for BMR estimation.
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        age_years: Age in years
        gender: 'male' or 'female'
    
    Returns:
        BMR in calories/day
    """
    if gender.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age_years) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age_years) - 161
    
    return round(bmr, 0)


def calculate_tdee(
    weight_kg: float,
    height_cm: float,
    age_years: int,
    gender: str,
    activity_level: str
) -> Dict:
    """
    Calculate Total Daily Energy Expenditure.
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        age_years: Age in years
        gender: 'male' or 'female'
        activity_level: One of the ACTIVITY_MULTIPLIERS keys
    
    Returns:
        Dictionary with BMR, TDEE, and goal-based calorie targets
    """
    bmr = calculate_bmr(weight_kg, height_cm, age_years, gender)
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    tdee = round(bmr * multiplier, 0)
    
    return {
        "bmr": int(bmr),
        "tdee": int(tdee),
        "activity_multiplier": multiplier,
        "targets": {
            "aggressive_loss": int(tdee - 750),   # ~1.5 lbs/week loss
            "moderate_loss": int(tdee - 500),     # ~1 lb/week loss
            "mild_loss": int(tdee - 250),         # ~0.5 lb/week loss
            "maintenance": int(tdee),
            "mild_gain": int(tdee + 250),         # ~0.5 lb/week gain
            "moderate_gain": int(tdee + 500)      # ~1 lb/week gain
        }
    }


def calculate_age(birth_date: date) -> int:
    """Calculate age from birth date."""
    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


# =============================================================================
# UNIT CONVERSIONS
# =============================================================================

def lbs_to_kg(lbs: float) -> float:
    """Convert pounds to kilograms."""
    return round(lbs * 0.453592, 2)


def kg_to_lbs(kg: float) -> float:
    """Convert kilograms to pounds."""
    return round(kg * 2.20462, 2)


def inches_to_cm(inches: float) -> float:
    """Convert inches to centimeters."""
    return round(inches * 2.54, 2)


def cm_to_inches(cm: float) -> float:
    """Convert centimeters to inches."""
    return round(cm / 2.54, 2)


def feet_inches_to_cm(feet: int, inches: int) -> float:
    """Convert feet and inches to centimeters."""
    total_inches = (feet * 12) + inches
    return inches_to_cm(total_inches)


def cm_to_feet_inches(cm: float) -> Tuple[int, int]:
    """Convert centimeters to feet and inches."""
    total_inches = cm / 2.54
    feet = int(total_inches // 12)
    inches = int(total_inches % 12)
    return feet, inches


# =============================================================================
# DATE HELPERS
# =============================================================================

def get_week_bounds(for_date: date = None) -> Tuple[date, date]:
    """Get the Monday-Sunday bounds for a given date's week."""
    if for_date is None:
        for_date = date.today()
    
    # Monday is 0, Sunday is 6
    days_since_monday = for_date.weekday()
    week_start = for_date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    
    return week_start, week_end


def get_month_bounds(for_date: date = None) -> Tuple[date, date]:
    """Get the first and last day of a given date's month."""
    if for_date is None:
        for_date = date.today()
    
    month_start = for_date.replace(day=1)
    
    # Get last day of month
    if for_date.month == 12:
        next_month = for_date.replace(year=for_date.year + 1, month=1, day=1)
    else:
        next_month = for_date.replace(month=for_date.month + 1, day=1)
    
    month_end = next_month - timedelta(days=1)
    
    return month_start, month_end


def format_date_display(d: date, include_year: bool = False) -> str:
    """Format date for display."""
    if include_year:
        return d.strftime("%b %d, %Y")
    return d.strftime("%b %d")


def format_time_display(t: datetime) -> str:
    """Format time for display."""
    return t.strftime("%I:%M %p").lstrip("0")


def get_relative_date_label(d: date) -> str:
    """Get a human-readable relative date label."""
    today = date.today()
    diff = (today - d).days
    
    if diff == 0:
        return "Today"
    elif diff == 1:
        return "Yesterday"
    elif diff < 7:
        return d.strftime("%A")  # Day name
    else:
        return format_date_display(d)


# =============================================================================
# CALORIE HELPERS
# =============================================================================

def calculate_calorie_variance(actual: int, target: int) -> Dict:
    """Calculate variance between actual and target calories."""
    variance = actual - target
    variance_pct = (variance / target * 100) if target > 0 else 0
    
    return {
        "variance": variance,
        "variance_pct": round(variance_pct, 1),
        "is_under": variance < 0,
        "is_over": variance > 0,
        "status": "under" if variance < 0 else ("over" if variance > 0 else "on_target")
    }


def get_calorie_color(actual: int, target: int, threshold_pct: float = 10) -> str:
    """
    Get a color code based on calorie variance.
    
    Returns:
        Hex color code: green (under), yellow (near), red (over)
    """
    variance = calculate_calorie_variance(actual, target)
    pct = abs(variance["variance_pct"])
    
    if variance["is_under"]:
        if pct > 20:
            return "#f59e0b"  # Yellow/warning - too far under
        return "#22c55e"  # Green - good
    elif variance["is_over"]:
        if pct <= threshold_pct:
            return "#f59e0b"  # Yellow - slightly over
        return "#ef4444"  # Red - significantly over
    else:
        return "#22c55e"  # Green - on target


def calculate_macro_percentages(protein_g: float, carbs_g: float, fat_g: float) -> Dict:
    """Calculate macro percentages from gram values."""
    protein_cal = protein_g * 4
    carbs_cal = carbs_g * 4
    fat_cal = fat_g * 9
    
    total_cal = protein_cal + carbs_cal + fat_cal
    
    if total_cal == 0:
        return {"protein_pct": 0, "carbs_pct": 0, "fat_pct": 0}
    
    return {
        "protein_pct": round(protein_cal / total_cal * 100, 1),
        "carbs_pct": round(carbs_cal / total_cal * 100, 1),
        "fat_pct": round(fat_cal / total_cal * 100, 1),
        "total_calories_from_macros": round(total_cal, 0)
    }


# =============================================================================
# ANALYTICS HELPERS
# =============================================================================

def calculate_rolling_average(values: List[float], window: int = 7) -> List[float]:
    """Calculate rolling average for a list of values."""
    if len(values) < window:
        return values
    
    result = []
    for i in range(len(values)):
        if i < window - 1:
            # Not enough data yet, use available
            result.append(sum(values[:i+1]) / (i + 1))
        else:
            # Full window available
            window_vals = values[i-window+1:i+1]
            result.append(sum(window_vals) / window)
    
    return [round(v, 1) for v in result]


def calculate_streak(dates: List[date]) -> int:
    """Calculate current consecutive day streak."""
    if not dates:
        return 0
    
    sorted_dates = sorted(set(dates), reverse=True)
    today = date.today()
    
    # Check if most recent is today or yesterday
    if sorted_dates[0] != today and sorted_dates[0] != today - timedelta(days=1):
        return 0
    
    streak = 1
    for i in range(len(sorted_dates) - 1):
        diff = (sorted_dates[i] - sorted_dates[i+1]).days
        if diff == 1:
            streak += 1
        else:
            break
    
    return streak


def format_calories(calories: int) -> str:
    """Format calories with thousands separator."""
    return f"{calories:,}"


def format_macro(grams: float) -> str:
    """Format macro grams for display."""
    if grams >= 100:
        return f"{grams:.0f}g"
    elif grams >= 10:
        return f"{grams:.1f}g"
    else:
        return f"{grams:.1f}g"


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for storage."""
    import re
    # Remove path separators and special characters
    sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
    # Ensure it doesn't start with a dot
    if sanitized.startswith('.'):
        sanitized = '_' + sanitized[1:]
    return sanitized
