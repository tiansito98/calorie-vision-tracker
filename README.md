# 🍎 Calorie Vision Tracker

A vision-powered calorie tracking application that uses Claude AI to analyze food photos and estimate nutritional content. Built for the "Twinkie Diet" principle: weight management through caloric deficit tracking.

## ✨ Features

- **📸 Photo-Based Logging**: Upload food photos and get AI-powered calorie estimates
- **🎯 Daily Target Tracking**: Compare intake against personalized caloric goals
- **📊 Analytics Dashboard**: Daily, weekly, and monthly trend analysis
- **🥗 Macro Tracking**: Protein, carbs, fat, fiber, and sugar estimation
- **📋 Meal Templates**: One-tap logging for frequently eaten meals
- **🧮 TDEE Calculator**: Built-in calculator for users without professional assessment
- **📧 Weekly Digests**: Automated email summaries (optional)
- **⏰ Meal Reminders**: Notification system for consistent logging
- **📤 Data Export**: CSV, Excel, and PDF report generation
- **✏️ Manual Adjustments**: Correct LLM estimates with adjustment tracking
- **🔒 Secure Auth**: User authentication with Supabase

## 🏗️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth |
| File Storage | Supabase Storage |
| AI Vision | Claude API (Anthropic) |
| Email | SendGrid (optional) |
| Hosting | Streamlit Cloud / Railway |

## 💰 Estimated Costs (Single User)

| Service | Monthly Cost |
|---------|--------------|
| Supabase | $0 (free tier) |
| Streamlit Cloud | $0 (free tier) |
| Claude API | $3-10 (5-10 photos/day) |
| SendGrid | $0 (free tier) |
| **Total** | **$3-10/month** |

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.9+
- Git
- Accounts: Supabase, Anthropic, GitHub, SendGrid (optional)

### Step 1: Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/calorie-vision-tracker.git
cd calorie-vision-tracker
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Set Up Supabase

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project (choose a region close to you)
3. Wait for project to provision (~2 minutes)
4. Go to **SQL Editor** in the left sidebar
5. Copy the entire contents of `sql/001_schema.sql`
6. Paste into the SQL editor and click **Run**
7. Verify tables were created in **Table Editor**

**Get your credentials:**
- Go to **Settings** → **API**
- Copy **Project URL** (this is `SUPABASE_URL`)
- Copy **anon public** key (this is `SUPABASE_ANON_KEY`)

**Create storage bucket:**
1. Go to **Storage** in the left sidebar
2. Click **New bucket**
3. Name it `food-images`
4. Toggle **Public bucket** to ON
5. Click **Create bucket**

### Step 4: Get Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create account or sign in
3. Go to **API Keys**
4. Create a new key and copy it (this is `ANTHROPIC_API_KEY`)

### Step 5: Set Up SendGrid (Optional - for email digests)

1. Go to [sendgrid.com](https://sendgrid.com) and create free account
2. Go to **Settings** → **API Keys**
3. Create API key with "Mail Send" permissions
4. Copy the key (this is `SENDGRID_API_KEY`)
5. Go to **Settings** → **Sender Authentication**
6. Verify a sender email (this is `SENDGRID_FROM_EMAIL`)

### Step 6: Configure Secrets

Create the secrets file:

```bash
mkdir -p .streamlit
nano .streamlit/secrets.toml  # or use your preferred editor
```

Add your credentials:

```toml
# Required
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key-here"
ANTHROPIC_API_KEY = "sk-ant-your-key-here"

# Optional (for email features)
SENDGRID_API_KEY = "SG.your-key-here"
SENDGRID_FROM_EMAIL = "your-verified-email@domain.com"
```

### Step 7: Run Locally

```bash
streamlit run app.py
```

The app should open at `http://localhost:8501`

---

## ✅ QA Testing Checklist

### Phase 1: Environment Verification
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `secrets.toml` configured with all required keys
- [ ] App starts without errors (`streamlit run app.py`)

### Phase 2: Database Connection
- [ ] SQL schema executed successfully in Supabase
- [ ] All 9 tables visible in Table Editor:
  - `dim_user_profile`
  - `dim_meal_type`
  - `dim_meal_template`
  - `fact_food_entry`
  - `fact_daily_summary`
  - `fact_weekly_digest`
  - `fact_notification_log`
  - Plus auth tables
- [ ] `dim_meal_type` pre-populated with 5 meal types
- [ ] Storage bucket `food-images` created and public

### Phase 3: Authentication
- [ ] **Sign Up**: Create new account with email/password
  - Profile automatically created
  - Redirected to dashboard
- [ ] **Sign Out**: Click logout, returned to login page
- [ ] **Sign In**: Log back in with credentials
- [ ] **Password Reset**: Request reset email (if email configured)

### Phase 4: Profile Setup
- [ ] Navigate to Settings → Profile tab
- [ ] Set display name
- [ ] Set calorie target
- [ ] Save and verify persistence

### Phase 5: TDEE Calculator
- [ ] Navigate to Settings → TDEE Calculator tab
- [ ] Enter test data:
  - Age: 45
  - Gender: Male
  - Weight: 180 lbs
  - Height: 5'10"
  - Activity: Moderately Active
- [ ] Click Calculate → BMR and TDEE displayed
- [ ] Select goal (e.g., "Moderate Loss")
- [ ] Click "Apply as My Target"
- [ ] Verify target updated in Profile tab

### Phase 6: Photo Food Logging
- [ ] Navigate to **Log Food** page
- [ ] Select **Upload Photo** tab
- [ ] Upload a clear food photo (e.g., plate of pasta)
- [ ] Click **Analyze Food**
- [ ] Verify results appear:
  - Food items listed
  - Calories estimated
  - Macros (protein, carbs, fat) estimated
  - Confidence score displayed
- [ ] Manually adjust calories (e.g., change 500 to 450)
- [ ] Verify "Adjusted" indicator appears
- [ ] Click **Save Entry**
- [ ] Verify entry appears on Dashboard

### Phase 7: Template Logging
- [ ] After saving a photo entry, click **Save as Template**
- [ ] Enter template name (e.g., "Morning Oatmeal")
- [ ] Navigate to **Meal Templates** page
- [ ] Verify template appears in list
- [ ] Click **Log** button on template
- [ ] Verify entry added to today's log
- [ ] Verify usage count incremented

### Phase 8: Manual Entry
- [ ] Navigate to **Log Food** → **Manual Entry** tab
- [ ] Fill out form:
  - Food name: "Apple"
  - Meal type: Snack
  - Calories: 95
  - Protein: 0.5g
- [ ] Save entry
- [ ] Verify appears on Dashboard

### Phase 9: Dashboard Validation
- [ ] Check top metrics:
  - Target shows correct value
  - Consumed = sum of all entries
  - Remaining = Target - Consumed
  - Entry count is accurate
- [ ] Progress bar reflects percentage correctly
- [ ] Color coding: green if under, red if over target
- [ ] Macro summary shows correct totals
- [ ] Date selector changes data displayed
- [ ] Empty state shows "Log Food" button when no entries

### Phase 10: History Page
- [ ] Navigate to **History**
- [ ] Verify all logged entries appear
- [ ] Test date range selector
- [ ] Expand a date group
- [ ] Delete an entry
- [ ] Verify it's removed from list
- [ ] Verify daily summary recalculates

### Phase 11: Analytics
- [ ] Log entries across multiple days (or use Supabase to insert test data)
- [ ] Navigate to **Analytics**
- [ ] Test time range selector (7, 14, 30, 90 days)
- [ ] Verify calorie trend chart displays
- [ ] Check target line is visible
- [ ] Verify stats:
  - Average daily calories
  - Days under/over target
  - Current streak count
- [ ] Check macro distribution pie chart
- [ ] Verify percentages sum to 100%

### Phase 12: Export Functions
- [ ] Navigate to **Export**
- [ ] Set date range
- [ ] Test each export type:
  - [ ] **CSV (Food Log)**: Downloads, opens in Excel/Sheets
  - [ ] **CSV (Daily Summaries)**: Downloads correctly
  - [ ] **Excel**: Downloads .xlsx, has 3 sheets (Summary, Daily, Log)
  - [ ] **PDF**: Downloads, opens with proper formatting

### Phase 13: Edge Cases
- [ ] Upload non-food image → should show low confidence warning
- [ ] Upload very large image (>10MB) → should handle gracefully
- [ ] Log on a past date → verify date handling
- [ ] Set calories to 0 → verify no division errors
- [ ] Rapid-fire multiple entries → no duplicates
- [ ] Test with empty database (new user) → proper empty states

### Phase 14: Row-Level Security
- [ ] Create second test account
- [ ] Log entries on second account
- [ ] Switch to first account
- [ ] Verify you CANNOT see second account's data
- [ ] This confirms RLS policies are working

### Phase 15: Email Features (if SendGrid configured)
- [ ] Enable weekly digest in Settings → Notifications
- [ ] Enable meal reminders
- [ ] Note: Actual sending requires scheduled job (cron)

---

## 🌐 Deployment

### Option A: Streamlit Community Cloud (FREE - Recommended)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Calorie Vision Tracker"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/calorie-vision-tracker.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub account
   - Select repository: `calorie-vision-tracker`
   - Main file path: `app.py`
   - Click "Deploy"

3. **Add Secrets**
   - In Streamlit Cloud dashboard, click on your app
   - Go to **Settings** → **Secrets**
   - Paste your `secrets.toml` contents
   - Click "Save"

4. **Reboot App**
   - Click "Reboot app" to apply secrets
   - Your app is now live!

### Option B: Railway ($5/month)

1. **Push to GitHub** (same as above)

2. **Deploy on Railway**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects Streamlit

3. **Add Environment Variables**
   - Go to your project → **Variables**
   - Add each secret as an environment variable:
     - `SUPABASE_URL`
     - `SUPABASE_ANON_KEY`
     - `ANTHROPIC_API_KEY`
     - `SENDGRID_API_KEY` (optional)
     - `SENDGRID_FROM_EMAIL` (optional)

4. **Configure Start Command**
   - In Settings, set start command:
   ```bash
   streamlit run app.py --server.port $PORT --server.address 0.0.0.0
   ```

5. **Generate Domain**
   - Go to **Settings** → **Domains**
   - Click "Generate Domain"

---

## 📁 Project Structure

```
calorie-vision-tracker/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .gitignore               # Git ignore rules
│
├── sql/
│   └── 001_schema.sql       # Database schema for Supabase
│
├── src/
│   ├── __init__.py
│   ├── config.py            # App configuration & constants
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── supabase_service.py   # Database operations
│   │   ├── claude_service.py     # AI image analysis
│   │   └── email_service.py      # SendGrid integration
│   │
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py       # TDEE calc, formatters, validators
│       └── export.py        # CSV, Excel, PDF generation
│
├── .streamlit/
│   └── secrets.toml         # API keys (DO NOT COMMIT)
│
├── tests/                   # Test files (future)
└── docs/                    # Documentation (future)
```

---

## 🔧 Configuration

### Customizing Meal Types

Edit `src/config.py` to modify meal types:

```python
MEAL_TYPES = {
    "breakfast": {"icon": "🌅", "order": 1, "time_range": (5, 11)},
    "lunch": {"icon": "☀️", "order": 2, "time_range": (11, 15)},
    # Add custom types...
}
```

### Adjusting TDEE Formulas

The app uses Mifflin-St Jeor equation. Modify in `src/utils/helpers.py`:

```python
def calculate_bmr(weight_kg, height_cm, age, gender):
    if gender == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
```

### Claude Prompt Tuning

Adjust the food analysis prompt in `src/config.py`:

```python
FOOD_ANALYSIS_PROMPT = """
Analyze this food image and estimate...
"""
```

---

## 🐛 Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt --upgrade
```

### Supabase connection fails
- Verify `SUPABASE_URL` starts with `https://`
- Verify `SUPABASE_ANON_KEY` is the "anon public" key, not the service key
- Check Supabase dashboard for API status

### Claude API errors
- Verify API key starts with `sk-ant-`
- Check [status.anthropic.com](https://status.anthropic.com) for outages
- Ensure billing is set up in Anthropic console

### Image upload fails
- Check image is under 10MB
- Supported formats: JPG, PNG, WEBP
- Verify `food-images` bucket exists and is public

### PDF export fails
- ReportLab may need system fonts
- Try: `pip install reportlab --upgrade`
- On Linux: `apt-get install libfreetype6-dev`

---

## 🔮 Future Enhancements

- [ ] Automated weekly digest scheduler (cron job)
- [ ] Push notifications for meal reminders
- [ ] PWA wrapper for mobile app experience
- [ ] Barcode scanning for packaged foods
- [ ] Restaurant menu integration
- [ ] Weight tracking over time
- [ ] Social features (sharing, challenges)
- [ ] Voice logging ("Log a banana")

---

## 📄 License

MIT License - Feel free to modify and use for personal projects.

---

## 🙏 Acknowledgments

- Inspired by Mark Haub's 2010 "Twinkie Diet" experiment
- Built with [Streamlit](https://streamlit.io), [Supabase](https://supabase.com), and [Claude](https://anthropic.com)

---

**Built with ❤️ for healthier living**
