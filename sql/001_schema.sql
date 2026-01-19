-- =============================================================================
-- CALORIE VISION TRACKER - DATABASE SCHEMA
-- Supabase PostgreSQL Schema
-- =============================================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- DIMENSION TABLES
-- =============================================================================

-- User Profile (extends Supabase auth.users)
CREATE TABLE dim_user_profile (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name VARCHAR(100),
    
    -- Biometrics
    date_of_birth DATE,
    gender VARCHAR(20), -- 'male', 'female', 'other'
    height_cm DECIMAL(5,2),
    current_weight_kg DECIMAL(5,2),
    activity_level VARCHAR(30), -- 'sedentary', 'light', 'moderate', 'active', 'very_active'
    
    -- Caloric Targets
    daily_calorie_target INTEGER NOT NULL DEFAULT 2000,
    target_calculation_method VARCHAR(30) DEFAULT 'manual', -- 'manual', 'tdee_calculated', 'professional'
    professional_assessment_date DATE,
    professional_notes TEXT,
    
    -- Macro Targets (optional percentages)
    protein_target_pct INTEGER DEFAULT 30,
    carbs_target_pct INTEGER DEFAULT 40,
    fat_target_pct INTEGER DEFAULT 30,
    
    -- Preferences
    timezone VARCHAR(50) DEFAULT 'America/Bogota',
    notification_enabled BOOLEAN DEFAULT TRUE,
    weekly_digest_enabled BOOLEAN DEFAULT TRUE,
    preferred_units VARCHAR(20) DEFAULT 'metric', -- 'metric', 'imperial'
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Meal Type Dimension
CREATE TABLE dim_meal_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_order INTEGER NOT NULL,
    icon VARCHAR(50),
    typical_time_start TIME,
    typical_time_end TIME,
    is_active BOOLEAN DEFAULT TRUE
);

-- Pre-populate meal types
INSERT INTO dim_meal_type (name, display_order, icon, typical_time_start, typical_time_end) VALUES
    ('breakfast', 1, '🌅', '06:00', '10:00'),
    ('morning_snack', 2, '🍎', '10:00', '12:00'),
    ('lunch', 3, '☀️', '12:00', '14:00'),
    ('afternoon_snack', 4, '🍪', '14:00', '17:00'),
    ('dinner', 5, '🌙', '17:00', '21:00'),
    ('evening_snack', 6, '🌃', '21:00', '23:59'),
    ('beverage', 7, '🥤', '00:00', '23:59');

-- Meal Templates (for quick logging of repeated meals)
CREATE TABLE dim_meal_template (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    template_name VARCHAR(100) NOT NULL,
    description TEXT,
    meal_type_id INTEGER REFERENCES dim_meal_type(id),
    
    -- Nutritional info (cached from original entry or manual)
    estimated_calories INTEGER NOT NULL,
    estimated_protein_g DECIMAL(6,2),
    estimated_carbs_g DECIMAL(6,2),
    estimated_fat_g DECIMAL(6,2),
    
    -- Reference image (optional)
    image_url TEXT,
    
    -- Usage tracking
    times_used INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(user_id, template_name)
);

-- =============================================================================
-- FACT TABLES
-- =============================================================================

-- Food Entry Fact Table (main transaction table)
CREATE TABLE fact_food_entry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    meal_type_id INTEGER NOT NULL REFERENCES dim_meal_type(id),
    
    -- Entry date/time
    entry_date DATE NOT NULL DEFAULT CURRENT_DATE,
    entry_time TIME DEFAULT CURRENT_TIME,
    entry_timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    -- Food description
    food_description TEXT NOT NULL,
    portion_description TEXT,
    
    -- Image data
    image_url TEXT,
    image_storage_path TEXT,
    
    -- LLM Analysis Results
    llm_analysis_raw JSONB, -- Full LLM response for debugging
    llm_model_used VARCHAR(50),
    llm_confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    
    -- Nutritional estimates (from LLM)
    estimated_calories INTEGER NOT NULL,
    estimated_protein_g DECIMAL(6,2),
    estimated_carbs_g DECIMAL(6,2),
    estimated_fat_g DECIMAL(6,2),
    estimated_fiber_g DECIMAL(6,2),
    estimated_sugar_g DECIMAL(6,2),
    
    -- Manual adjustments
    manual_calories INTEGER,
    manual_protein_g DECIMAL(6,2),
    manual_carbs_g DECIMAL(6,2),
    manual_fat_g DECIMAL(6,2),
    adjustment_reason TEXT,
    was_manually_adjusted BOOLEAN DEFAULT FALSE,
    
    -- Final values (manual if adjusted, else estimated)
    final_calories INTEGER GENERATED ALWAYS AS (COALESCE(manual_calories, estimated_calories)) STORED,
    final_protein_g DECIMAL(6,2) GENERATED ALWAYS AS (COALESCE(manual_protein_g, estimated_protein_g)) STORED,
    final_carbs_g DECIMAL(6,2) GENERATED ALWAYS AS (COALESCE(manual_carbs_g, estimated_carbs_g)) STORED,
    final_fat_g DECIMAL(6,2) GENERATED ALWAYS AS (COALESCE(manual_fat_g, estimated_fat_g)) STORED,
    
    -- Source tracking
    source_type VARCHAR(30) DEFAULT 'image_upload', -- 'image_upload', 'template', 'manual_entry', 'quick_add'
    template_id UUID REFERENCES dim_meal_template(id),
    
    -- Metadata
    notes TEXT,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Daily Summary Fact Table (aggregated, can be materialized view or table)
CREATE TABLE fact_daily_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    summary_date DATE NOT NULL,
    
    -- Caloric data
    total_calories INTEGER DEFAULT 0,
    calorie_target INTEGER,
    calorie_variance INTEGER GENERATED ALWAYS AS (total_calories - calorie_target) STORED,
    calorie_variance_pct DECIMAL(5,2),
    
    -- Macro data
    total_protein_g DECIMAL(7,2) DEFAULT 0,
    total_carbs_g DECIMAL(7,2) DEFAULT 0,
    total_fat_g DECIMAL(7,2) DEFAULT 0,
    total_fiber_g DECIMAL(7,2) DEFAULT 0,
    
    -- Entry counts
    total_entries INTEGER DEFAULT 0,
    meals_logged INTEGER DEFAULT 0,
    snacks_logged INTEGER DEFAULT 0,
    beverages_logged INTEGER DEFAULT 0,
    
    -- Logging completeness
    has_breakfast BOOLEAN DEFAULT FALSE,
    has_lunch BOOLEAN DEFAULT FALSE,
    has_dinner BOOLEAN DEFAULT FALSE,
    logging_completeness_score DECIMAL(3,2), -- 0.00 to 1.00
    
    -- Running averages (for trend analysis)
    rolling_7day_avg_calories DECIMAL(7,2),
    rolling_30day_avg_calories DECIMAL(7,2),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, summary_date)
);

-- Weekly Digest Log (track sent digests)
CREATE TABLE fact_weekly_digest (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    
    -- Summary data at time of digest
    total_calories INTEGER,
    avg_daily_calories DECIMAL(7,2),
    days_logged INTEGER,
    days_under_target INTEGER,
    days_over_target INTEGER,
    
    -- Digest metadata
    digest_content JSONB,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    email_sent_to VARCHAR(255),
    
    UNIQUE(user_id, week_start_date)
);

-- Notification/Reminder Log
CREATE TABLE fact_notification_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    notification_type VARCHAR(50) NOT NULL, -- 'meal_reminder', 'weekly_digest', 'milestone'
    meal_type_id INTEGER REFERENCES dim_meal_type(id),
    
    scheduled_for TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,
    was_sent BOOLEAN DEFAULT FALSE,
    
    message_content TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

CREATE INDEX idx_food_entry_user_date ON fact_food_entry(user_id, entry_date DESC);
CREATE INDEX idx_food_entry_date ON fact_food_entry(entry_date DESC);
CREATE INDEX idx_food_entry_meal_type ON fact_food_entry(meal_type_id);
CREATE INDEX idx_daily_summary_user_date ON fact_daily_summary(user_id, summary_date DESC);
CREATE INDEX idx_meal_template_user ON dim_meal_template(user_id);
CREATE INDEX idx_notification_log_user ON fact_notification_log(user_id, scheduled_for);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================

ALTER TABLE dim_user_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_meal_template ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_food_entry ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_daily_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_weekly_digest ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_notification_log ENABLE ROW LEVEL SECURITY;

-- User can only see their own data
CREATE POLICY "Users can view own profile" ON dim_user_profile
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own templates" ON dim_meal_template
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own food entries" ON fact_food_entry
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own daily summaries" ON fact_daily_summary
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own digests" ON fact_weekly_digest
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own notifications" ON fact_notification_log
    FOR ALL USING (auth.uid() = user_id);

-- Meal types are public read
CREATE POLICY "Meal types are public" ON dim_meal_type
    FOR SELECT USING (true);

-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_user_profile_timestamp
    BEFORE UPDATE ON dim_user_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_meal_template_timestamp
    BEFORE UPDATE ON dim_meal_template
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_food_entry_timestamp
    BEFORE UPDATE ON fact_food_entry
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_daily_summary_timestamp
    BEFORE UPDATE ON fact_daily_summary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Function to create user profile on signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO dim_user_profile (user_id, display_name)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'display_name');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Function to refresh daily summary
CREATE OR REPLACE FUNCTION refresh_daily_summary(p_user_id UUID, p_date DATE)
RETURNS VOID AS $$
DECLARE
    v_target INTEGER;
BEGIN
    -- Get user's calorie target
    SELECT daily_calorie_target INTO v_target
    FROM dim_user_profile
    WHERE user_id = p_user_id;

    -- Upsert daily summary
    INSERT INTO fact_daily_summary (
        user_id, summary_date, calorie_target,
        total_calories, total_protein_g, total_carbs_g, total_fat_g, total_fiber_g,
        total_entries, meals_logged, snacks_logged, beverages_logged,
        has_breakfast, has_lunch, has_dinner, logging_completeness_score
    )
    SELECT 
        p_user_id,
        p_date,
        v_target,
        COALESCE(SUM(final_calories), 0),
        COALESCE(SUM(final_protein_g), 0),
        COALESCE(SUM(final_carbs_g), 0),
        COALESCE(SUM(final_fat_g), 0),
        COALESCE(SUM(estimated_fiber_g), 0),
        COUNT(*),
        COUNT(*) FILTER (WHERE meal_type_id IN (1, 3, 5)),
        COUNT(*) FILTER (WHERE meal_type_id IN (2, 4, 6)),
        COUNT(*) FILTER (WHERE meal_type_id = 7),
        COUNT(*) FILTER (WHERE meal_type_id = 1) > 0,
        COUNT(*) FILTER (WHERE meal_type_id = 3) > 0,
        COUNT(*) FILTER (WHERE meal_type_id = 5) > 0,
        CASE 
            WHEN COUNT(*) FILTER (WHERE meal_type_id IN (1, 3, 5)) >= 3 THEN 1.0
            ELSE COUNT(*) FILTER (WHERE meal_type_id IN (1, 3, 5))::DECIMAL / 3
        END
    FROM fact_food_entry
    WHERE user_id = p_user_id 
      AND entry_date = p_date 
      AND is_deleted = FALSE
    ON CONFLICT (user_id, summary_date) 
    DO UPDATE SET
        total_calories = EXCLUDED.total_calories,
        total_protein_g = EXCLUDED.total_protein_g,
        total_carbs_g = EXCLUDED.total_carbs_g,
        total_fat_g = EXCLUDED.total_fat_g,
        total_fiber_g = EXCLUDED.total_fiber_g,
        total_entries = EXCLUDED.total_entries,
        meals_logged = EXCLUDED.meals_logged,
        snacks_logged = EXCLUDED.snacks_logged,
        beverages_logged = EXCLUDED.beverages_logged,
        has_breakfast = EXCLUDED.has_breakfast,
        has_lunch = EXCLUDED.has_lunch,
        has_dinner = EXCLUDED.has_dinner,
        logging_completeness_score = EXCLUDED.logging_completeness_score,
        calorie_variance_pct = CASE 
            WHEN v_target > 0 THEN ((EXCLUDED.total_calories - v_target)::DECIMAL / v_target * 100)
            ELSE 0
        END,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-refresh daily summary on food entry changes
CREATE OR REPLACE FUNCTION trigger_refresh_daily_summary()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM refresh_daily_summary(OLD.user_id, OLD.entry_date);
        RETURN OLD;
    ELSE
        PERFORM refresh_daily_summary(NEW.user_id, NEW.entry_date);
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_food_entry_change
    AFTER INSERT OR UPDATE OR DELETE ON fact_food_entry
    FOR EACH ROW EXECUTE FUNCTION trigger_refresh_daily_summary();

-- =============================================================================
-- STORAGE BUCKET FOR IMAGES
-- =============================================================================

-- Run this in Supabase SQL editor or dashboard:
-- INSERT INTO storage.buckets (id, name, public) VALUES ('food-images', 'food-images', false);

-- Storage policies (run in Supabase dashboard):
-- CREATE POLICY "Users can upload own images" ON storage.objects
--     FOR INSERT WITH CHECK (bucket_id = 'food-images' AND auth.uid()::text = (storage.foldername(name))[1]);
-- CREATE POLICY "Users can view own images" ON storage.objects
--     FOR SELECT USING (bucket_id = 'food-images' AND auth.uid()::text = (storage.foldername(name))[1]);
