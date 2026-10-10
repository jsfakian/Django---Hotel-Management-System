-- Extracted verbatim from DELIVERABLES-Task4-SystemArchitecture.md
-- Source: Task 4 System Architecture & Design
-- Extraction date: 2026-02-20

-- SQL Block 1
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) NOT NULL REFERENCES roles(name),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- SQL Block 2
CREATE TABLE bookings (
    id BIGSERIAL PRIMARY KEY,
    room_id BIGINT NOT NULL REFERENCES rooms(id),
    guest_id BIGINT NOT NULL REFERENCES guests(id),
    travel_agency_id BIGINT REFERENCES travel_agencies(id),
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'confirmed',
    base_price DECIMAL(10,2) NOT NULL,
    actual_price DECIMAL(10,2),
    number_of_guests INT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bookings_room_id ON bookings(room_id);
CREATE INDEX idx_bookings_guest_id ON bookings(guest_id);
CREATE INDEX idx_bookings_check_in_out ON bookings(check_in, check_out);
CREATE INDEX idx_bookings_status ON bookings(status);

-- SQL Block 3
CREATE TABLE pricing_history (
    id BIGSERIAL PRIMARY KEY,
    room_id BIGINT NOT NULL REFERENCES rooms(id),
    date DATE NOT NULL,
    base_price DECIMAL(10,2),
    dynamic_price DECIMAL(10,2),
    competitor_price DECIMAL(10,2),
    occupancy_rate DECIMAL(5,2),
    demand_score DECIMAL(5,2),
    season VARCHAR(20),
    weekday INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_pricing_history_room_date ON pricing_history(room_id, date);
CREATE INDEX idx_pricing_history_date ON pricing_history(date);

-- SQL Block 4
CREATE TABLE dashboard_executive_metrics (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT NOT NULL REFERENCES properties(id),
    metric_date DATE NOT NULL,
    
    -- Executive KPIs
    total_revenue DECIMAL(12,2),
    avg_daily_rate DECIMAL(10,2),
    occupancy_rate DECIMAL(5,2),
    revpar DECIMAL(10,2),
    booking_count INTEGER,
    
    -- Trends
    revenue_trend_30d JSONB,  -- {date: value, ...}
    occupancy_trend_30d JSONB,
    adr_trend_30d JSONB,
    
    -- Comparisons
    yoy_revenue_change DECIMAL(5,2),
    yoy_occupancy_change DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(property_id, metric_date),
    INDEX idx_property_date (property_id, metric_date)
);

-- SQL Block 5
CREATE TABLE dashboard_operational_status (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT NOT NULL REFERENCES properties(id),
    status_date DATE NOT NULL,
    status_time TIMESTAMP NOT NULL,
    
    -- Room Status
    occupied_count INTEGER,
    vacant_count INTEGER,
    cleaning_count INTEGER,
    maintenance_count INTEGER,
    blocked_count INTEGER,
    
    -- Check-in/Check-out
    checkouts_scheduled INTEGER,
    checkins_scheduled INTEGER,
    
    -- Task Status
    housekeeping_tasks_pending INTEGER,
    housekeeping_tasks_in_progress INTEGER,
    maintenance_tickets_pending INTEGER,
    
    -- Guest-related
    active_guests_count INTEGER,
    guests_with_special_requests INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_property_datetime (property_id, status_date, status_time)
);

-- SQL Block 6
CREATE TABLE dashboard_revenue_metrics (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT NOT NULL REFERENCES properties(id),
    metric_date DATE NOT NULL,
    
    -- Revenue
    total_revenue DECIMAL(12,2),
    revenue_direct DECIMAL(12,2),
    revenue_ota DECIMAL(12,2),
    revenue_agency DECIMAL(12,2),
    
    -- Pricing
    avg_daily_rate DECIMAL(10,2),
    revpar DECIMAL(10,2),
    dynamic_pricing_uplift DECIMAL(5,2),
    
    -- Occupancy
    occupancy_rate DECIMAL(5,2),
    occupancy_count INTEGER,
    
    -- Bookings
    booking_count INTEGER,
    cancellation_count INTEGER,
    cancellation_rate DECIMAL(5,2),
    noshow_count INTEGER,
    
    -- Forecast
    revenue_forecast_30d DECIMAL(12,2),
    occupancy_forecast_30d DECIMAL(5,2),
    
    metrics_by_source JSONB,  -- {direct: {...}, ota: {...}, agency: {...}}
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(property_id, metric_date),
    INDEX idx_property_date (property_id, metric_date)
);

-- SQL Block 7
CREATE TABLE dashboard_guest_analytics (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT NOT NULL REFERENCES properties(id),
    analytics_date DATE NOT NULL,
    
    -- Guest counts
    total_unique_guests INTEGER,
    new_guests INTEGER,
    returning_guests INTEGER,
    repeat_booking_rate DECIMAL(5,2),
    
    -- Behavior
    avg_booking_lead_days INTEGER,
    avg_length_of_stay DECIMAL(5,2),
    
    -- Satisfaction
    avg_review_score DECIMAL(3,2),
    avg_nps INTEGER,
    review_rate DECIMAL(5,2),
    complaint_count INTEGER,
    complaint_resolution_rate DECIMAL(5,2),
    
    -- Churn
    retention_rate DECIMAL(5,2),
    churn_rate DECIMAL(5,2),
    at_risk_guests INTEGER,
    
    -- Personalization
    recommendations_generated INTEGER,
    recommendations_accepted INTEGER,
    upsell_conversions INTEGER,
    cross_sell_conversions INTEGER,
    personalization_revenue_uplift DECIMAL(5,2),
    
    guest_segments JSONB,  -- {leisure: %, business: %, family: %, ...}
    geographic_breakdown JSONB,  -- {country: count, ...}
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_property_date (property_id, analytics_date)
);

-- SQL Block 8
CREATE TABLE scheduled_reports (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    created_by INT NOT NULL REFERENCES auth_user(id) ON DELETE SET NULL,
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    report_type VARCHAR(50) NOT NULL,  -- 'daily_operational', 'weekly_performance', 'monthly_executive', etc.
    
    -- Scheduling
    schedule_type VARCHAR(20) NOT NULL,  -- 'daily', 'weekly', 'monthly', 'custom'
    schedule_day INT,  -- Day of month for monthly reports
    schedule_dow INT,  -- Day of week for weekly reports (0-6)
    schedule_time TIME NOT NULL,  -- Time to generate report (UTC)
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Recipients
    recipient_emails TEXT[] NOT NULL,  -- Array of email addresses
    include_managers BOOLEAN DEFAULT true,  -- Include property managers
    include_owner BOOLEAN DEFAULT false,  -- Include property owner
    
    -- Configuration
    include_charts BOOLEAN DEFAULT true,
    include_summary BOOLEAN DEFAULT true,
    include_detailed_data BOOLEAN DEFAULT true,
    custom_filters JSONB,  -- Custom filters for report
    metric_selection JSONB,  -- Selected metrics to include
    
    -- Output
    export_formats TEXT[] DEFAULT ARRAY['pdf'],  -- ['pdf', 'excel', 'csv']
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_generated_at TIMESTAMP,
    next_scheduled_at TIMESTAMP,
    consecutive_failures INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(property_id, name),
    INDEX idx_property_active (property_id, is_active),
    INDEX idx_next_scheduled (next_scheduled_at)
);

CREATE TABLE report_executions (
    id SERIAL PRIMARY KEY,
    scheduled_report_id INT NOT NULL REFERENCES scheduled_reports(id) ON DELETE CASCADE,
    
    execution_status VARCHAR(20) NOT NULL,  -- 'pending', 'generating', 'generated', 'failed'
    
    -- Files generated
    pdf_file_path VARCHAR(500),
    excel_file_path VARCHAR(500),
    csv_file_path VARCHAR(500),
    
    -- Email delivery
    email_status VARCHAR(20),  -- 'pending', 'sent', 'failed'
    email_sent_at TIMESTAMP,
    email_recipients TEXT[],
    
    -- Metadata
    data_date_from DATE,
    data_date_to DATE,
    metrics_snapshot JSONB,  -- Snapshot of KPIs for this report
    
    execution_time_seconds INT,
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_scheduled_report (scheduled_report_id),
    INDEX idx_status (execution_status),
    INDEX idx_created (created_at)
);

CREATE TABLE report_delivery_tracking (
    id SERIAL PRIMARY KEY,
    report_execution_id INT NOT NULL REFERENCES report_executions(id) ON DELETE CASCADE,
    
    recipient_email VARCHAR(255) NOT NULL,
    delivery_status VARCHAR(20),  -- 'pending', 'sent', 'bounced', 'opened', 'failed'
    
    opened_at TIMESTAMP,
    click_count INT DEFAULT 0,
    last_clicked_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_recipient (recipient_email),
    INDEX idx_execution (report_execution_id),
    INDEX idx_status (delivery_status)
);

-- SQL Block 9
-- Occupancy Forecasts
CREATE TABLE occupancy_forecasts (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    forecast_date DATE NOT NULL,
    target_date DATE NOT NULL,
    predicted_occupancy DECIMAL(5,2) NOT NULL,
    lower_bound DECIMAL(5,2),
    upper_bound DECIMAL(5,2),
    model_type VARCHAR(20), -- prophet|sarima|ensemble
    actual_occupancy DECIMAL(5,2),
    forecast_error DECIMAL(5,2),
    created_at TIMESTAMP,
    UNIQUE(property_id, forecast_date, target_date, model_type),
    INDEX idx_property_target (property_id, target_date)
);

-- Revenue Forecasts
CREATE TABLE revenue_forecasts (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    forecast_date DATE NOT NULL,
    target_date DATE NOT NULL,
    predicted_revenue DECIMAL(12,2) NOT NULL,
    lower_bound DECIMAL(12,2),
    upper_bound DECIMAL(12,2),
    model_type VARCHAR(20),
    predicted_occupancy DECIMAL(5,2),
    avg_daily_rate DECIMAL(10,2),
    actual_revenue DECIMAL(12,2),
    forecast_error DECIMAL(12,2),
    forecast_error_pct DECIMAL(5,2),
    created_at TIMESTAMP,
    UNIQUE(property_id, forecast_date, target_date, model_type)
);

-- Cancellation Predictions
CREATE TABLE cancellation_predictions (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    booking_id INT,
    prediction_date DATE NOT NULL,
    prediction_time TIMESTAMP NOT NULL,
    cancellation_risk_score DECIMAL(5,2) NOT NULL,
    risk_level VARCHAR(20), -- low|medium|high
    lead_time_days INT,
    booking_source VARCHAR(50),
    intervention_flag BOOLEAN DEFAULT false,
    actually_cancelled BOOLEAN,
    cancellation_date DATE,
    created_at TIMESTAMP,
    INDEX idx_property_risk_level (property_id, risk_level),
    INDEX idx_booking (booking_id)
);

-- No-Show Predictions
CREATE TABLE noshow_predictions (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    booking_id INT,
    prediction_date DATE NOT NULL,
    prediction_time TIMESTAMP NOT NULL,
    noshow_risk_score DECIMAL(5,2) NOT NULL,
    risk_level VARCHAR(20), -- low|medium|high
    customer_country VARCHAR(100),
    payment_confirmed BOOLEAN,
    overbooking_flag BOOLEAN DEFAULT false,
    overbooking_factor DECIMAL(3,2),
    actually_noshow BOOLEAN,
    created_at TIMESTAMP,
    INDEX idx_property_risk_level (property_id, risk_level),
    INDEX idx_overbooking (overbooking_flag)
);

-- Model Metrics for Monitoring
CREATE TABLE forecasting_model_metrics (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    evaluation_date DATE NOT NULL,
    evaluation_period VARCHAR(20), -- 7day|14day|30day|90day
    mae DECIMAL(12,4),             -- Mean Absolute Error
    rmse DECIMAL(12,4),            -- Root Mean Squared Error
    mape DECIMAL(5,2),             -- Mean Absolute Percentage Error
    r_squared DECIMAL(5,4),        -- R-squared coefficient
    precision DECIMAL(5,4),        -- For classification models
    recall DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    roc_auc DECIMAL(5,4),
    predictions_count INT,
    is_acceptable BOOLEAN,
    needs_retraining BOOLEAN,
    created_at TIMESTAMP,
    UNIQUE(property_id, model_name, evaluation_date),
    INDEX idx_health_check (is_acceptable, needs_retraining)
);

