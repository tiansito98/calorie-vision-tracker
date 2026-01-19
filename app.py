"""
Calorie Vision Tracker
======================
Main application entry point.

A vision-based calorie tracking app using Claude AI for food image analysis.
"""

import streamlit as st
from datetime import date, datetime, timedelta
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import get_config, validate_config, MEAL_TYPES
from src.services.supabase_service import get_supabase_client
from src.services.claude_service import create_claude_service
from src.utils.helpers import (
    calculate_calorie_variance, 
    get_calorie_color, 
    format_calories,
    get_relative_date_label
)

# Page configuration
st.set_page_config(
    page_title="Calorie Vision Tracker",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Card style */
    .stCard {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Progress bar */
    .calorie-progress {
        height: 12px;
        border-radius: 6px;
        background: #e5e7eb;
        overflow: hidden;
    }
    
    .calorie-progress-fill {
        height: 100%;
        border-radius: 6px;
        transition: width 0.3s ease;
    }
    
    /* Food entry card */
    .food-entry {
        background: #f9fafb;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 4px solid #3b82f6;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Button styles */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* Success/warning colors */
    .success-text { color: #22c55e; }
    .warning-text { color: #f59e0b; }
    .danger-text { color: #ef4444; }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "authenticated": False,
        "user": None,
        "user_profile": None,
        "current_page": "dashboard",
        "selected_date": date.today(),
        "analysis_result": None,
        "show_adjustment_form": False,
        "editing_entry_id": None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def login_page(db):
    """Render the login/signup page."""
    st.markdown("# 🍎 Calorie Vision Tracker")
    st.markdown("Track your calories with AI-powered food image analysis")
    
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            
            if submitted:
                if email and password:
                    result = db.sign_in(email, password)
                    if result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.user = result["user"]
                        st.rerun()
                    else:
                        st.error(f"Login failed: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("Please enter both email and password")
        
        if st.button("Forgot Password?"):
            st.session_state.show_reset = True
    
    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            display_name = st.text_input("Display Name")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            submitted = st.form_submit_button("Create Account", use_container_width=True)
            
            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords don't match")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters")
                elif new_email and new_password:
                    result = db.sign_up(new_email, new_password, display_name)
                    if result["success"]:
                        st.success("Account created! Please check your email to verify, then sign in.")
                    else:
                        st.error(f"Signup failed: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("Please fill in all fields")


def sidebar_navigation(db):
    """Render sidebar with navigation and user info."""
    with st.sidebar:
        # User info
        profile = st.session_state.user_profile
        if profile:
            st.markdown(f"### 👋 {profile.get('display_name', 'User')}")
            st.markdown(f"**Target:** {profile.get('daily_calorie_target', 2000):,} cal/day")
        
        st.divider()
        
        # Navigation
        st.markdown("### Navigation")
        
        pages = {
            "dashboard": ("📊", "Dashboard"),
            "log_food": ("📸", "Log Food"),
            "history": ("📅", "History"),
            "analytics": ("📈", "Analytics"),
            "templates": ("⭐", "Meal Templates"),
            "profile": ("⚙️", "Settings"),
            "export": ("📤", "Export Data")
        }
        
        for page_key, (icon, label) in pages.items():
            if st.button(f"{icon} {label}", key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.divider()
        
        # Quick stats
        today = date.today()
        summary = db.get_daily_summary(st.session_state.user.id, today)
        
        if summary:
            target = profile.get("daily_calorie_target", 2000) if profile else 2000
            consumed = summary.get("total_calories", 0)
            remaining = target - consumed
            
            st.markdown("### Today's Progress")
            st.metric("Consumed", f"{consumed:,} cal")
            
            color = "green" if remaining >= 0 else "red"
            st.markdown(f"**Remaining:** :{color}[{remaining:,} cal]")
        
        st.divider()
        
        # Sign out
        if st.button("🚪 Sign Out", use_container_width=True):
            db.sign_out()
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.user_profile = None
            st.rerun()


def dashboard_page(db, config):
    """Render the main dashboard."""
    st.markdown("# 📊 Dashboard")
    
    profile = st.session_state.user_profile
    user_id = st.session_state.user.id
    today = date.today()
    
    # Date selector
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        selected_date = st.date_input(
            "Select Date",
            value=st.session_state.selected_date,
            max_value=today
        )
        st.session_state.selected_date = selected_date
    
    # Get data for selected date
    summary = db.get_daily_summary(user_id, selected_date)
    entries = db.get_food_entries_by_date(user_id, selected_date)
    
    target = profile.get("daily_calorie_target", 2000) if profile else 2000
    consumed = summary.get("total_calories", 0) if summary else 0
    remaining = target - consumed
    
    # Top metrics
    st.markdown(f"### {get_relative_date_label(selected_date)}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 Target", f"{target:,}")
    
    with col2:
        st.metric("🍽️ Consumed", f"{consumed:,}")
    
    with col3:
        delta_color = "normal" if remaining >= 0 else "inverse"
        st.metric("📊 Remaining", f"{remaining:,}", delta=f"{remaining:,}", delta_color=delta_color)
    
    with col4:
        entries_count = len(entries) if entries else 0
        st.metric("📝 Entries", entries_count)
    
    # Progress bar
    progress_pct = min(consumed / target * 100, 100) if target > 0 else 0
    bar_color = get_calorie_color(consumed, target)
    
    st.markdown(f"""
    <div class="calorie-progress">
        <div class="calorie-progress-fill" style="width: {progress_pct}%; background: {bar_color};"></div>
    </div>
    <p style="text-align: center; margin-top: 0.5rem; color: #6b7280;">
        {progress_pct:.1f}% of daily target
    </p>
    """, unsafe_allow_html=True)
    
    # Macros summary
    if summary:
        st.markdown("### Macros")
        mcol1, mcol2, mcol3 = st.columns(3)
        
        with mcol1:
            protein = summary.get("total_protein_g", 0) or 0
            st.metric("🥩 Protein", f"{protein:.0f}g")
        
        with mcol2:
            carbs = summary.get("total_carbs_g", 0) or 0
            st.metric("🍞 Carbs", f"{carbs:.0f}g")
        
        with mcol3:
            fat = summary.get("total_fat_g", 0) or 0
            st.metric("🥑 Fat", f"{fat:.0f}g")
    
    # Today's entries
    st.markdown("### Food Log")
    
    if entries:
        for entry in entries:
            meal_info = entry.get("dim_meal_type", {})
            meal_icon = meal_info.get("icon", "🍽️") if isinstance(meal_info, dict) else "🍽️"
            meal_name = meal_info.get("name", "Meal") if isinstance(meal_info, dict) else "Meal"
            
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{meal_icon} {entry.get('food_description', 'Food')}**")
                    if entry.get("portion_description"):
                        st.caption(entry["portion_description"])
                
                with col2:
                    st.markdown(f"**{entry.get('final_calories', 0):,} cal**")
                    if entry.get("was_manually_adjusted"):
                        st.caption("✏️ Adjusted")
                
                with col3:
                    st.caption(entry.get("entry_time", "")[:5] if entry.get("entry_time") else "")
                
                st.divider()
    else:
        st.info("No food logged yet. Tap 'Log Food' to add your first entry!")
        if st.button("📸 Log Food Now", use_container_width=True):
            st.session_state.current_page = "log_food"
            st.rerun()


def log_food_page(db, config):
    """Render the food logging page."""
    st.markdown("# 📸 Log Food")
    
    user_id = st.session_state.user.id
    
    # Tabs for different logging methods
    tab1, tab2, tab3 = st.tabs(["📷 Photo", "⭐ Template", "✏️ Manual"])
    
    with tab1:
        st.markdown("### Upload a food photo")
        
        uploaded_file = st.file_uploader(
            "Take a photo or upload an image",
            type=["jpg", "jpeg", "png", "webp"],
            help="For best results, capture the entire plate with good lighting"
        )
        
        # Meal type and date selection
        col1, col2 = st.columns(2)
        with col1:
            meal_types = db.get_meal_types()
            meal_options = {m["id"]: f"{m.get('icon', '')} {m['name'].replace('_', ' ').title()}" for m in meal_types}
            selected_meal_type = st.selectbox(
                "Meal Type",
                options=list(meal_options.keys()),
                format_func=lambda x: meal_options[x]
            )
        
        with col2:
            entry_date = st.date_input("Date", value=date.today(), max_value=date.today())
        
        additional_context = st.text_input(
            "Additional context (optional)",
            placeholder="e.g., Colombian breakfast, restaurant portion..."
        )
        
        if uploaded_file is not None:
            # Display image
            st.image(uploaded_file, caption="Uploaded food photo", use_container_width=True)
            
            if st.button("🔍 Analyze Food", type="primary", use_container_width=True):
                with st.spinner("Analyzing your food with AI..."):
                    # Create Claude service
                    claude = create_claude_service(config.ANTHROPIC_API_KEY)
                    
                    # Analyze image
                    result = claude.analyze_food_image(
                        uploaded_file.getvalue(),
                        uploaded_file.name,
                        additional_context
                    )
                    
                    st.session_state.analysis_result = result
                    st.session_state.pending_meal_type = selected_meal_type
                    st.session_state.pending_date = entry_date
                    st.session_state.pending_image = uploaded_file.getvalue()
                    st.session_state.pending_filename = uploaded_file.name
        
        # Show analysis result
        if st.session_state.analysis_result:
            result = st.session_state.analysis_result
            
            if result.success:
                st.success(f"Analysis complete! Confidence: {result.confidence:.0%}")
                
                st.markdown("### Analysis Results")
                st.markdown(f"**{result.description}**")
                
                # Show detected items
                if result.food_items:
                    st.markdown("**Detected Items:**")
                    for item in result.food_items:
                        st.markdown(f"- {item['name']} ({item['portion']}): {item['calories']} cal")
                
                # Editable results
                st.markdown("### Nutritional Estimates")
                
                col1, col2 = st.columns(2)
                with col1:
                    final_calories = st.number_input(
                        "Calories",
                        value=result.total_calories,
                        min_value=0,
                        max_value=5000,
                        step=10
                    )
                    final_protein = st.number_input(
                        "Protein (g)",
                        value=float(result.protein_g),
                        min_value=0.0,
                        max_value=500.0,
                        step=1.0
                    )
                
                with col2:
                    final_carbs = st.number_input(
                        "Carbs (g)",
                        value=float(result.carbs_g),
                        min_value=0.0,
                        max_value=500.0,
                        step=1.0
                    )
                    final_fat = st.number_input(
                        "Fat (g)",
                        value=float(result.fat_g),
                        min_value=0.0,
                        max_value=500.0,
                        step=1.0
                    )
                
                notes = st.text_area("Notes (optional)", placeholder="Any notes about this meal...")
                
                # Check if manually adjusted
                was_adjusted = (
                    final_calories != result.total_calories or
                    final_protein != result.protein_g or
                    final_carbs != result.carbs_g or
                    final_fat != result.fat_g
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Save Entry", type="primary", use_container_width=True):
                        # Upload image
                        image_result = db.upload_food_image(
                            user_id,
                            st.session_state.pending_image,
                            st.session_state.pending_filename
                        )
                        
                        # Create entry
                        entry_data = {
                            "user_id": user_id,
                            "meal_type_id": st.session_state.pending_meal_type,
                            "entry_date": st.session_state.pending_date.isoformat(),
                            "food_description": result.description,
                            "image_url": image_result.get("url", ""),
                            "image_storage_path": image_result.get("path", ""),
                            "llm_analysis_raw": result.raw_response,
                            "llm_model_used": config.CLAUDE_MODEL,
                            "llm_confidence_score": result.confidence,
                            "estimated_calories": result.total_calories,
                            "estimated_protein_g": result.protein_g,
                            "estimated_carbs_g": result.carbs_g,
                            "estimated_fat_g": result.fat_g,
                            "estimated_fiber_g": result.fiber_g,
                            "estimated_sugar_g": result.sugar_g,
                            "was_manually_adjusted": was_adjusted,
                            "notes": notes,
                            "source_type": "image_upload"
                        }
                        
                        if was_adjusted:
                            entry_data["manual_calories"] = final_calories
                            entry_data["manual_protein_g"] = final_protein
                            entry_data["manual_carbs_g"] = final_carbs
                            entry_data["manual_fat_g"] = final_fat
                        
                        save_result = db.create_food_entry(entry_data)
                        
                        if save_result["success"]:
                            st.success("Food entry saved!")
                            st.session_state.analysis_result = None
                            st.balloons()
                        else:
                            st.error(f"Failed to save: {save_result.get('error', 'Unknown error')}")
                
                with col2:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.session_state.analysis_result = None
                        st.rerun()
                
                # Option to save as template
                st.divider()
                with st.expander("💾 Save as Meal Template"):
                    template_name = st.text_input("Template Name", value=result.description)
                    if st.button("Save Template"):
                        template_data = {
                            "user_id": user_id,
                            "template_name": template_name,
                            "description": result.description,
                            "meal_type_id": st.session_state.pending_meal_type,
                            "estimated_calories": final_calories,
                            "estimated_protein_g": final_protein,
                            "estimated_carbs_g": final_carbs,
                            "estimated_fat_g": final_fat
                        }
                        db.create_meal_template(template_data)
                        st.success("Template saved!")
            
            else:
                st.error(f"Analysis failed: {result.error}")
    
    with tab2:
        st.markdown("### Quick log from templates")
        
        templates = db.get_meal_templates(user_id)
        
        if templates:
            for template in templates:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{template['template_name']}**")
                        st.caption(f"Used {template.get('times_used', 0)} times")
                    
                    with col2:
                        st.markdown(f"**{template['estimated_calories']:,} cal**")
                    
                    with col3:
                        if st.button("➕ Log", key=f"log_template_{template['id']}"):
                            entry_data = {
                                "user_id": user_id,
                                "meal_type_id": template.get("meal_type_id", 1),
                                "entry_date": date.today().isoformat(),
                                "food_description": template["template_name"],
                                "estimated_calories": template["estimated_calories"],
                                "estimated_protein_g": template.get("estimated_protein_g"),
                                "estimated_carbs_g": template.get("estimated_carbs_g"),
                                "estimated_fat_g": template.get("estimated_fat_g"),
                                "source_type": "template",
                                "template_id": template["id"]
                            }
                            
                            result = db.create_food_entry(entry_data)
                            if result["success"]:
                                db.increment_template_usage(template["id"])
                                st.success(f"Logged: {template['template_name']}")
                                st.rerun()
                    
                    st.divider()
        else:
            st.info("No templates yet. Analyze a photo and save it as a template for quick logging!")
    
    with tab3:
        st.markdown("### Manual entry")
        
        with st.form("manual_entry_form"):
            description = st.text_input("Food Description", placeholder="e.g., Grilled chicken with rice")
            
            col1, col2 = st.columns(2)
            with col1:
                meal_types = db.get_meal_types()
                meal_options = {m["id"]: f"{m.get('icon', '')} {m['name'].replace('_', ' ').title()}" for m in meal_types}
                meal_type = st.selectbox(
                    "Meal Type",
                    options=list(meal_options.keys()),
                    format_func=lambda x: meal_options[x],
                    key="manual_meal_type"
                )
            
            with col2:
                manual_date = st.date_input("Date", value=date.today(), max_value=date.today(), key="manual_date")
            
            st.markdown("**Nutrition**")
            col1, col2 = st.columns(2)
            with col1:
                manual_calories = st.number_input("Calories", min_value=0, max_value=5000, value=300, step=10)
                manual_protein = st.number_input("Protein (g)", min_value=0.0, max_value=500.0, value=0.0, step=1.0)
            
            with col2:
                manual_carbs = st.number_input("Carbs (g)", min_value=0.0, max_value=500.0, value=0.0, step=1.0)
                manual_fat = st.number_input("Fat (g)", min_value=0.0, max_value=500.0, value=0.0, step=1.0)
            
            manual_notes = st.text_area("Notes (optional)")
            
            if st.form_submit_button("Save Entry", type="primary", use_container_width=True):
                if description:
                    entry_data = {
                        "user_id": user_id,
                        "meal_type_id": meal_type,
                        "entry_date": manual_date.isoformat(),
                        "food_description": description,
                        "estimated_calories": manual_calories,
                        "estimated_protein_g": manual_protein if manual_protein > 0 else None,
                        "estimated_carbs_g": manual_carbs if manual_carbs > 0 else None,
                        "estimated_fat_g": manual_fat if manual_fat > 0 else None,
                        "notes": manual_notes,
                        "source_type": "manual_entry"
                    }
                    
                    result = db.create_food_entry(entry_data)
                    if result["success"]:
                        st.success("Entry saved!")
                        st.balloons()
                    else:
                        st.error(f"Failed to save: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("Please enter a food description")


def history_page(db, config):
    """Render the history page."""
    st.markdown("# 📅 History")
    
    user_id = st.session_state.user.id
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "From",
            value=date.today() - timedelta(days=7),
            max_value=date.today()
        )
    with col2:
        end_date = st.date_input(
            "To",
            value=date.today(),
            max_value=date.today()
        )
    
    if start_date > end_date:
        st.error("Start date must be before end date")
        return
    
    # Get entries
    entries = db.get_food_entries_range(user_id, start_date, end_date)
    summaries = db.get_daily_summaries_range(user_id, start_date, end_date)
    
    if not entries:
        st.info("No entries found for this date range.")
        return
    
    # Summary stats
    total_calories = sum(e.get("final_calories", 0) for e in entries)
    avg_daily = total_calories / ((end_date - start_date).days + 1)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Entries", len(entries))
    with col2:
        st.metric("Total Calories", f"{total_calories:,}")
    with col3:
        st.metric("Daily Average", f"{avg_daily:,.0f}")
    
    st.divider()
    
    # Group by date
    from collections import defaultdict
    by_date = defaultdict(list)
    for entry in entries:
        by_date[entry["entry_date"]].append(entry)
    
    for entry_date in sorted(by_date.keys(), reverse=True):
        day_entries = by_date[entry_date]
        day_total = sum(e.get("final_calories", 0) for e in day_entries)
        
        with st.expander(f"📅 {entry_date} - {day_total:,} cal ({len(day_entries)} entries)"):
            for entry in day_entries:
                meal_info = entry.get("dim_meal_type", {})
                meal_icon = meal_info.get("icon", "🍽️") if isinstance(meal_info, dict) else "🍽️"
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{meal_icon} {entry.get('food_description', 'Food')}**")
                    if entry.get("notes"):
                        st.caption(entry["notes"])
                
                with col2:
                    st.markdown(f"**{entry.get('final_calories', 0):,} cal**")
                
                with col3:
                    if st.button("🗑️", key=f"del_{entry['id']}", help="Delete entry"):
                        if db.delete_food_entry(entry["id"])["success"]:
                            st.success("Deleted!")
                            st.rerun()
                
                st.divider()


def analytics_page(db, config):
    """Render the analytics page."""
    st.markdown("# 📈 Analytics")
    
    user_id = st.session_state.user.id
    profile = st.session_state.user_profile
    target = profile.get("daily_calorie_target", 2000) if profile else 2000
    
    # Time range selector
    time_range = st.selectbox(
        "Time Range",
        options=["Last 7 Days", "Last 14 Days", "Last 30 Days", "Last 90 Days"],
        index=1
    )
    
    days_map = {"Last 7 Days": 7, "Last 14 Days": 14, "Last 30 Days": 30, "Last 90 Days": 90}
    days = days_map[time_range]
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    summaries = db.get_daily_summaries_range(user_id, start_date, end_date)
    
    if not summaries:
        st.info("Not enough data for analytics. Start logging your meals!")
        return
    
    # Prepare data for charts
    import pandas as pd
    
    df = pd.DataFrame(summaries)
    df["summary_date"] = pd.to_datetime(df["summary_date"])
    df = df.sort_values("summary_date")
    
    # Calorie trend chart
    st.markdown("### 📊 Calorie Trend")
    
    import plotly.express as px
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Add calorie bars
    fig.add_trace(go.Bar(
        x=df["summary_date"],
        y=df["total_calories"],
        name="Calories",
        marker_color=df["total_calories"].apply(lambda x: "#22c55e" if x <= target else "#ef4444")
    ))
    
    # Add target line
    fig.add_trace(go.Scatter(
        x=df["summary_date"],
        y=[target] * len(df),
        mode="lines",
        name="Target",
        line=dict(color="#3b82f6", dash="dash")
    ))
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Calories",
        hovermode="x unified",
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Stats summary
    col1, col2, col3, col4 = st.columns(4)
    
    avg_calories = df["total_calories"].mean()
    days_under = (df["total_calories"] < target).sum()
    days_over = (df["total_calories"] > target).sum()
    
    with col1:
        st.metric("Average Daily", f"{avg_calories:,.0f} cal")
    
    with col2:
        variance = avg_calories - target
        st.metric("vs Target", f"{variance:+,.0f} cal")
    
    with col3:
        st.metric("Days Under Target", days_under, delta=f"{days_under}/{len(df)}")
    
    with col4:
        streak = db.get_streak_info(user_id)
        st.metric("Current Streak", f"{streak.get('current_streak', 0)} days")
    
    # Macro breakdown
    st.markdown("### 🥗 Macro Distribution")
    
    total_protein = df["total_protein_g"].sum()
    total_carbs = df["total_carbs_g"].sum()
    total_fat = df["total_fat_g"].sum()
    
    if total_protein or total_carbs or total_fat:
        macro_fig = go.Figure(data=[go.Pie(
            labels=["Protein", "Carbs", "Fat"],
            values=[total_protein * 4, total_carbs * 4, total_fat * 9],  # Convert to calories
            marker_colors=["#ef4444", "#3b82f6", "#f59e0b"],
            hole=0.4
        )])
        
        macro_fig.update_layout(
            annotations=[dict(text="Macros", x=0.5, y=0.5, font_size=16, showarrow=False)]
        )
        
        st.plotly_chart(macro_fig, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Protein", f"{total_protein:,.0f}g")
        with col2:
            st.metric("Total Carbs", f"{total_carbs:,.0f}g")
        with col3:
            st.metric("Total Fat", f"{total_fat:,.0f}g")


def templates_page(db, config):
    """Render the meal templates page."""
    st.markdown("# ⭐ Meal Templates")
    st.markdown("Save your frequent meals for quick one-tap logging")
    
    user_id = st.session_state.user.id
    templates = db.get_meal_templates(user_id)
    
    # Create new template
    with st.expander("➕ Create New Template"):
        with st.form("new_template_form"):
            name = st.text_input("Template Name", placeholder="e.g., Morning Oatmeal")
            description = st.text_area("Description (optional)")
            
            meal_types = db.get_meal_types()
            meal_options = {m["id"]: f"{m.get('icon', '')} {m['name'].replace('_', ' ').title()}" for m in meal_types}
            meal_type = st.selectbox(
                "Meal Type",
                options=list(meal_options.keys()),
                format_func=lambda x: meal_options[x]
            )
            
            col1, col2 = st.columns(2)
            with col1:
                calories = st.number_input("Calories", min_value=0, value=300)
                protein = st.number_input("Protein (g)", min_value=0.0, value=0.0)
            with col2:
                carbs = st.number_input("Carbs (g)", min_value=0.0, value=0.0)
                fat = st.number_input("Fat (g)", min_value=0.0, value=0.0)
            
            if st.form_submit_button("Create Template", type="primary"):
                if name:
                    template_data = {
                        "user_id": user_id,
                        "template_name": name,
                        "description": description,
                        "meal_type_id": meal_type,
                        "estimated_calories": calories,
                        "estimated_protein_g": protein if protein > 0 else None,
                        "estimated_carbs_g": carbs if carbs > 0 else None,
                        "estimated_fat_g": fat if fat > 0 else None
                    }
                    result = db.create_meal_template(template_data)
                    if result["success"]:
                        st.success("Template created!")
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("Please enter a name")
    
    st.divider()
    
    # List templates
    if templates:
        for template in templates:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"### {template['template_name']}")
                    if template.get("description"):
                        st.caption(template["description"])
                    st.caption(f"Used {template.get('times_used', 0)} times")
                
                with col2:
                    st.markdown(f"**{template['estimated_calories']:,} cal**")
                    if template.get("estimated_protein_g"):
                        st.caption(f"P: {template['estimated_protein_g']:.0f}g")
                
                with col3:
                    if st.button("🗑️ Delete", key=f"del_template_{template['id']}"):
                        db.delete_meal_template(template["id"])
                        st.rerun()
                
                st.divider()
    else:
        st.info("No templates yet. Create one above or save an analyzed meal as a template!")


def profile_page(db, config):
    """Render the profile/settings page."""
    st.markdown("# ⚙️ Settings")
    
    user_id = st.session_state.user.id
    profile = st.session_state.user_profile or {}
    
    tab1, tab2, tab3 = st.tabs(["Profile", "TDEE Calculator", "Notifications"])
    
    with tab1:
        st.markdown("### Profile Settings")
        
        with st.form("profile_form"):
            display_name = st.text_input("Display Name", value=profile.get("display_name", ""))
            
            st.markdown("**Calorie Target**")
            target_method = st.radio(
                "How was your target determined?",
                options=["manual", "tdee_calculated", "professional"],
                format_func=lambda x: {
                    "manual": "Manual Entry",
                    "tdee_calculated": "TDEE Calculator",
                    "professional": "Professional Assessment"
                }[x],
                index=["manual", "tdee_calculated", "professional"].index(
                    profile.get("target_calculation_method", "manual")
                )
            )
            
            calorie_target = st.number_input(
                "Daily Calorie Target",
                min_value=1000,
                max_value=5000,
                value=profile.get("daily_calorie_target", 2000),
                step=50
            )
            
            st.markdown("**Macro Targets (%)**")
            col1, col2, col3 = st.columns(3)
            with col1:
                protein_pct = st.number_input("Protein %", min_value=0, max_value=100, value=profile.get("protein_target_pct", 30))
            with col2:
                carbs_pct = st.number_input("Carbs %", min_value=0, max_value=100, value=profile.get("carbs_target_pct", 40))
            with col3:
                fat_pct = st.number_input("Fat %", min_value=0, max_value=100, value=profile.get("fat_target_pct", 30))
            
            total_pct = protein_pct + carbs_pct + fat_pct
            if total_pct != 100:
                st.warning(f"Macro percentages should add up to 100% (currently {total_pct}%)")
            
            if st.form_submit_button("Save Profile", type="primary"):
                update_data = {
                    "display_name": display_name,
                    "daily_calorie_target": calorie_target,
                    "target_calculation_method": target_method,
                    "protein_target_pct": protein_pct,
                    "carbs_target_pct": carbs_pct,
                    "fat_target_pct": fat_pct
                }
                
                result = db.update_user_profile(user_id, update_data)
                if result["success"]:
                    st.session_state.user_profile = db.get_user_profile(user_id)
                    st.success("Profile updated!")
                else:
                    st.error(f"Failed to update: {result.get('error', 'Unknown error')}")
    
    with tab2:
        st.markdown("### TDEE Calculator")
        st.markdown("Calculate your Total Daily Energy Expenditure")
        
        from src.utils.helpers import calculate_tdee, ACTIVITY_DESCRIPTIONS
        
        with st.form("tdee_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                weight = st.number_input("Weight (kg)", min_value=30.0, max_value=300.0, value=70.0, step=0.5)
                height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.5)
            
            with col2:
                age = st.number_input("Age", min_value=15, max_value=100, value=30)
                gender = st.selectbox("Gender", options=["male", "female"])
            
            activity = st.selectbox(
                "Activity Level",
                options=list(ACTIVITY_DESCRIPTIONS.keys()),
                format_func=lambda x: f"{x.replace('_', ' ').title()} - {ACTIVITY_DESCRIPTIONS[x]}"
            )
            
            if st.form_submit_button("Calculate TDEE", type="primary"):
                result = calculate_tdee(weight, height, age, gender, activity)
                
                st.success(f"Your estimated TDEE: **{result['tdee']:,} calories/day**")
                
                st.markdown("**Calorie Targets by Goal:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Weight Loss:**")
                    st.markdown(f"- Aggressive (-750): {result['targets']['aggressive_loss']:,} cal")
                    st.markdown(f"- Moderate (-500): {result['targets']['moderate_loss']:,} cal")
                    st.markdown(f"- Mild (-250): {result['targets']['mild_loss']:,} cal")
                
                with col2:
                    st.markdown("**Weight Gain:**")
                    st.markdown(f"- Mild (+250): {result['targets']['mild_gain']:,} cal")
                    st.markdown(f"- Moderate (+500): {result['targets']['moderate_gain']:,} cal")
                
                if st.button("Use TDEE as my target"):
                    db.update_user_profile(user_id, {
                        "daily_calorie_target": result["tdee"],
                        "target_calculation_method": "tdee_calculated"
                    })
                    st.session_state.user_profile = db.get_user_profile(user_id)
                    st.success("Target updated!")
                    st.rerun()
    
    with tab3:
        st.markdown("### Notification Settings")
        
        notifications = st.toggle(
            "Enable meal reminders",
            value=profile.get("notification_enabled", True)
        )
        
        weekly_digest = st.toggle(
            "Weekly email digest",
            value=profile.get("weekly_digest_enabled", True)
        )
        
        if st.button("Save Notification Settings"):
            db.update_user_profile(user_id, {
                "notification_enabled": notifications,
                "weekly_digest_enabled": weekly_digest
            })
            st.session_state.user_profile = db.get_user_profile(user_id)
            st.success("Settings saved!")


def export_page(db, config):
    """Render the data export page."""
    st.markdown("# 📤 Export Data")
    
    user_id = st.session_state.user.id
    profile = st.session_state.user_profile
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "From",
            value=date.today() - timedelta(days=30),
            max_value=date.today()
        )
    with col2:
        end_date = st.date_input(
            "To",
            value=date.today(),
            max_value=date.today()
        )
    
    # Get data
    entries = db.get_food_entries_range(user_id, start_date, end_date)
    summaries = db.get_daily_summaries_range(user_id, start_date, end_date)
    
    st.info(f"Found {len(entries)} food entries and {len(summaries)} daily summaries")
    
    st.divider()
    
    from src.utils.export import (
        export_food_entries_csv,
        export_daily_summaries_csv,
        export_to_excel,
        generate_pdf_report,
        calculate_export_stats
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📋 CSV")
        
        if st.button("Export Food Log (CSV)", use_container_width=True):
            csv_data = export_food_entries_csv(entries)
            st.download_button(
                "⬇️ Download Food Log",
                data=csv_data,
                file_name=f"food_log_{start_date}_{end_date}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        if st.button("Export Daily Summaries (CSV)", use_container_width=True):
            csv_data = export_daily_summaries_csv(summaries)
            st.download_button(
                "⬇️ Download Summaries",
                data=csv_data,
                file_name=f"daily_summaries_{start_date}_{end_date}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        st.markdown("### 📊 Excel")
        
        if st.button("Export All Data (Excel)", use_container_width=True):
            excel_data = export_to_excel(entries, summaries, profile, (start_date, end_date))
            st.download_button(
                "⬇️ Download Excel",
                data=excel_data,
                file_name=f"calorie_tracker_{start_date}_{end_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col3:
        st.markdown("### 📄 PDF Report")
        
        if st.button("Generate PDF Report", use_container_width=True):
            stats = calculate_export_stats(summaries)
            pdf_data = generate_pdf_report(summaries, profile, (start_date, end_date), stats)
            st.download_button(
                "⬇️ Download PDF",
                data=pdf_data,
                file_name=f"calorie_report_{start_date}_{end_date}.pdf",
                mime="application/pdf",
                use_container_width=True
            )


def main():
    """Main application entry point."""
    init_session_state()
    
    # Load configuration
    config = get_config()
    is_valid, missing = validate_config(config)
    
    if not is_valid:
        st.error(f"Missing configuration: {', '.join(missing)}")
        st.info("Please configure the required secrets in .streamlit/secrets.toml or environment variables.")
        st.stop()
    
    # Initialize database client
    db = get_supabase_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
    
    # Check authentication
    if not st.session_state.authenticated:
        login_page(db)
        return
    
    # Load user profile if not loaded
    if st.session_state.user and not st.session_state.user_profile:
        st.session_state.user_profile = db.get_user_profile(st.session_state.user.id)
    
    # Render sidebar
    sidebar_navigation(db)
    
    # Route to current page
    page = st.session_state.current_page
    
    if page == "dashboard":
        dashboard_page(db, config)
    elif page == "log_food":
        log_food_page(db, config)
    elif page == "history":
        history_page(db, config)
    elif page == "analytics":
        analytics_page(db, config)
    elif page == "templates":
        templates_page(db, config)
    elif page == "profile":
        profile_page(db, config)
    elif page == "export":
        export_page(db, config)
    else:
        dashboard_page(db, config)


if __name__ == "__main__":
    main()
