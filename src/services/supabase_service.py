"""
Supabase Service
================
Handles all database operations and authentication with Supabase.
"""

from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Any
import streamlit as st
from supabase import create_client, Client
import json


class SupabaseService:
    """Service class for all Supabase database operations."""
    
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)
    
    # =========================================================================
    # AUTHENTICATION
    # =========================================================================
    
    def sign_up(self, email: str, password: str, display_name: str = "") -> Dict:
        """Register a new user."""
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {"display_name": display_name}
                }
            })
            return {"success": True, "user": response.user, "session": response.session}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sign_in(self, email: str, password: str) -> Dict:
        """Sign in an existing user."""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {"success": True, "user": response.user, "session": response.session}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sign_out(self) -> bool:
        """Sign out the current user."""
        try:
            self.client.auth.sign_out()
            return True
        except:
            return False
    
    def get_current_user(self):
        """Get the currently authenticated user."""
        try:
            return self.client.auth.get_user()
        except:
            return None
    
    def reset_password(self, email: str) -> Dict:
        """Send password reset email."""
        try:
            self.client.auth.reset_password_email(email)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # USER PROFILE
    # =========================================================================
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile by user ID."""
        try:
            response = self.client.table("dim_user_profile")\
                .select("*")\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            return response.data
        except:
            return None
    
    def update_user_profile(self, user_id: str, profile_data: Dict) -> Dict:
        """Update user profile."""
        try:
            response = self.client.table("dim_user_profile")\
                .update(profile_data)\
                .eq("user_id", user_id)\
                .execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_user_profile(self, user_id: str, profile_data: Dict) -> Dict:
        """Create initial user profile."""
        try:
            profile_data["user_id"] = user_id
            response = self.client.table("dim_user_profile")\
                .insert(profile_data)\
                .execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # MEAL TYPES
    # =========================================================================
    
    def get_meal_types(self) -> List[Dict]:
        """Get all active meal types."""
        try:
            response = self.client.table("dim_meal_type")\
                .select("*")\
                .eq("is_active", True)\
                .order("display_order")\
                .execute()
            return response.data
        except:
            return []
    
    # =========================================================================
    # FOOD ENTRIES
    # =========================================================================
    
    def create_food_entry(self, entry_data: Dict) -> Dict:
        """Create a new food entry."""
        try:
            response = self.client.table("fact_food_entry")\
                .insert(entry_data)\
                .execute()
            return {"success": True, "data": response.data[0] if response.data else None}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_food_entry(self, entry_id: str, entry_data: Dict) -> Dict:
        """Update an existing food entry."""
        try:
            response = self.client.table("fact_food_entry")\
                .update(entry_data)\
                .eq("id", entry_id)\
                .execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_food_entry(self, entry_id: str) -> Dict:
        """Soft delete a food entry."""
        try:
            response = self.client.table("fact_food_entry")\
                .update({"is_deleted": True})\
                .eq("id", entry_id)\
                .execute()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_food_entries_by_date(self, user_id: str, entry_date: date) -> List[Dict]:
        """Get all food entries for a specific date."""
        try:
            response = self.client.table("fact_food_entry")\
                .select("*, dim_meal_type(name, icon)")\
                .eq("user_id", user_id)\
                .eq("entry_date", entry_date.isoformat())\
                .eq("is_deleted", False)\
                .order("entry_time")\
                .execute()
            return response.data
        except:
            return []
    
    def get_food_entries_range(self, user_id: str, start_date: date, end_date: date) -> List[Dict]:
        """Get food entries within a date range."""
        try:
            response = self.client.table("fact_food_entry")\
                .select("*, dim_meal_type(name, icon)")\
                .eq("user_id", user_id)\
                .gte("entry_date", start_date.isoformat())\
                .lte("entry_date", end_date.isoformat())\
                .eq("is_deleted", False)\
                .order("entry_date", desc=True)\
                .order("entry_time", desc=True)\
                .execute()
            return response.data
        except:
            return []
    
    def get_recent_food_entries(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get most recent food entries."""
        try:
            response = self.client.table("fact_food_entry")\
                .select("*, dim_meal_type(name, icon)")\
                .eq("user_id", user_id)\
                .eq("is_deleted", False)\
                .order("entry_timestamp", desc=True)\
                .limit(limit)\
                .execute()
            return response.data
        except:
            return []
    
    # =========================================================================
    # MEAL TEMPLATES
    # =========================================================================
    
    def get_meal_templates(self, user_id: str) -> List[Dict]:
        """Get all active meal templates for a user."""
        try:
            response = self.client.table("dim_meal_template")\
                .select("*, dim_meal_type(name, icon)")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .order("times_used", desc=True)\
                .execute()
            return response.data
        except:
            return []
    
    def create_meal_template(self, template_data: Dict) -> Dict:
        """Create a new meal template."""
        try:
            response = self.client.table("dim_meal_template")\
                .insert(template_data)\
                .execute()
            return {"success": True, "data": response.data[0] if response.data else None}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_meal_template(self, template_id: str, template_data: Dict) -> Dict:
        """Update a meal template."""
        try:
            response = self.client.table("dim_meal_template")\
                .update(template_data)\
                .eq("id", template_id)\
                .execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def increment_template_usage(self, template_id: str) -> None:
        """Increment the usage counter for a template."""
        try:
            # Get current count
            response = self.client.table("dim_meal_template")\
                .select("times_used")\
                .eq("id", template_id)\
                .single()\
                .execute()
            
            current = response.data.get("times_used", 0)
            
            # Update
            self.client.table("dim_meal_template")\
                .update({"times_used": current + 1, "last_used_at": datetime.now().isoformat()})\
                .eq("id", template_id)\
                .execute()
        except:
            pass
    
    def delete_meal_template(self, template_id: str) -> Dict:
        """Soft delete a meal template."""
        try:
            response = self.client.table("dim_meal_template")\
                .update({"is_active": False})\
                .eq("id", template_id)\
                .execute()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # DAILY SUMMARIES
    # =========================================================================
    
    def get_daily_summary(self, user_id: str, summary_date: date) -> Optional[Dict]:
        """Get daily summary for a specific date."""
        try:
            response = self.client.table("fact_daily_summary")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("summary_date", summary_date.isoformat())\
                .single()\
                .execute()
            return response.data
        except:
            return None
    
    def get_daily_summaries_range(self, user_id: str, start_date: date, end_date: date) -> List[Dict]:
        """Get daily summaries within a date range."""
        try:
            response = self.client.table("fact_daily_summary")\
                .select("*")\
                .eq("user_id", user_id)\
                .gte("summary_date", start_date.isoformat())\
                .lte("summary_date", end_date.isoformat())\
                .order("summary_date")\
                .execute()
            return response.data
        except:
            return []
    
    def get_weekly_summary(self, user_id: str, week_start: date) -> Dict:
        """Get aggregated weekly summary."""
        week_end = week_start + timedelta(days=6)
        summaries = self.get_daily_summaries_range(user_id, week_start, week_end)
        
        if not summaries:
            return {}
        
        total_calories = sum(s.get("total_calories", 0) for s in summaries)
        days_logged = len(summaries)
        
        return {
            "week_start": week_start,
            "week_end": week_end,
            "days_logged": days_logged,
            "total_calories": total_calories,
            "avg_daily_calories": total_calories / days_logged if days_logged > 0 else 0,
            "total_protein_g": sum(s.get("total_protein_g", 0) or 0 for s in summaries),
            "total_carbs_g": sum(s.get("total_carbs_g", 0) or 0 for s in summaries),
            "total_fat_g": sum(s.get("total_fat_g", 0) or 0 for s in summaries),
            "summaries": summaries
        }
    
    # =========================================================================
    # WEEKLY DIGESTS
    # =========================================================================
    
    def create_weekly_digest(self, digest_data: Dict) -> Dict:
        """Create a weekly digest record."""
        try:
            response = self.client.table("fact_weekly_digest")\
                .insert(digest_data)\
                .execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_latest_digest(self, user_id: str) -> Optional[Dict]:
        """Get the most recent weekly digest."""
        try:
            response = self.client.table("fact_weekly_digest")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("week_start_date", desc=True)\
                .limit(1)\
                .single()\
                .execute()
            return response.data
        except:
            return None
    
    # =========================================================================
    # IMAGE STORAGE
    # =========================================================================
    
    def upload_food_image(self, user_id: str, file_data: bytes, filename: str) -> Dict:
        """Upload a food image to Supabase storage."""
        try:
            path = f"{user_id}/{datetime.now().strftime('%Y/%m/%d')}/{filename}"
            response = self.client.storage.from_("food-images").upload(
                path, 
                file_data,
                {"content-type": "image/jpeg"}
            )
            
            # Get public URL
            url = self.client.storage.from_("food-images").get_public_url(path)
            
            return {"success": True, "path": path, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_image_url(self, path: str) -> str:
        """Get the public URL for an image."""
        try:
            return self.client.storage.from_("food-images").get_public_url(path)
        except:
            return ""
    
    # =========================================================================
    # ANALYTICS QUERIES
    # =========================================================================
    
    def get_calorie_trend(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get calorie trend for the last N days."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        return self.get_daily_summaries_range(user_id, start_date, end_date)
    
    def get_meal_type_distribution(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get distribution of calories by meal type."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        try:
            response = self.client.table("fact_food_entry")\
                .select("meal_type_id, final_calories, dim_meal_type(name)")\
                .eq("user_id", user_id)\
                .gte("entry_date", start_date.isoformat())\
                .lte("entry_date", end_date.isoformat())\
                .eq("is_deleted", False)\
                .execute()
            return response.data
        except:
            return []
    
    def get_streak_info(self, user_id: str) -> Dict:
        """Calculate current logging streak."""
        try:
            response = self.client.table("fact_daily_summary")\
                .select("summary_date")\
                .eq("user_id", user_id)\
                .order("summary_date", desc=True)\
                .limit(100)\
                .execute()
            
            if not response.data:
                return {"current_streak": 0, "longest_streak": 0}
            
            dates = [datetime.strptime(d["summary_date"], "%Y-%m-%d").date() 
                    for d in response.data]
            
            # Calculate current streak
            current_streak = 0
            check_date = date.today()
            
            for d in dates:
                if d == check_date or d == check_date - timedelta(days=1):
                    current_streak += 1
                    check_date = d - timedelta(days=1)
                else:
                    break
            
            return {
                "current_streak": current_streak,
                "total_days_logged": len(dates)
            }
        except:
            return {"current_streak": 0, "total_days_logged": 0}


@st.cache_resource
def get_supabase_client(url: str, key: str) -> SupabaseService:
    """Get cached Supabase service instance."""
    return SupabaseService(url, key)
