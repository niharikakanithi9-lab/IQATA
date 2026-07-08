CREATE TABLE IF NOT EXISTS test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    module TEXT,
    browser TEXT,
    environment TEXT,
    priority REAL,
    active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



-- ===========================
-- Test Runs
-- ===========================

CREATE TABLE IF NOT EXISTS test_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_case_id INTEGER,
    status TEXT,
    execution_time REAL,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    failure_reason TEXT,
    suggested_root_cause TEXT,
    screenshot_url TEXT,
    log_url TEXT,

    FOREIGN KEY(test_case_id)
    REFERENCES test_cases(id)
);



-- ===========================
-- ML Predictions
-- ===========================

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_case_id INTEGER,
    risk_score REAL,
    predicted_failure INTEGER,
    confidence REAL,
    model_version TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(test_case_id)
    REFERENCES test_cases(id)
);



-- ===========================
-- Metrics
-- ===========================

CREATE TABLE IF NOT EXISTS test_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_case_id INTEGER,
    failure_rate REAL,
    avg_execution_time REAL,
    last_execution TIMESTAMP,
    total_runs INTEGER,

    FOREIGN KEY(test_case_id)
    REFERENCES test_cases(id)
);