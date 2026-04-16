-- Argo Profiles Table (actual data ke hisaab se)
CREATE TABLE IF NOT EXISTS argo_profiles (
    id                  SERIAL PRIMARY KEY,
    float_id            VARCHAR(20)     NOT NULL,
    date                TIMESTAMP       NOT NULL,
    latitude            DOUBLE PRECISION NOT NULL,
    longitude           DOUBLE PRECISION NOT NULL,
    pressure            REAL,
    temperature         REAL,
    salinity            REAL,
    data_centre         VARCHAR(10),
    platform_type       VARCHAR(50),
    positioning_system  VARCHAR(20),
    project_name        VARCHAR(100),
    created_at          TIMESTAMP DEFAULT NOW(),
    UNIQUE (float_id, date, latitude, longitude, pressure)
);

-- Float Metadata Table
CREATE TABLE IF NOT EXISTS float_metadata (
    float_id            VARCHAR(20) PRIMARY KEY,
    data_centre         VARCHAR(10),
    platform_type       VARCHAR(50),
    positioning_system  VARCHAR(20),
    project_name        VARCHAR(100),
    first_seen          TIMESTAMP,
    last_seen           TIMESTAMP,
    total_profiles      INTEGER DEFAULT 0
);

-- Fast queries ke liye indexes
CREATE INDEX IF NOT EXISTS idx_argo_date     
    ON argo_profiles(date);
CREATE INDEX IF NOT EXISTS idx_argo_location 
    ON argo_profiles(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_argo_float    
    ON argo_profiles(float_id);
CREATE INDEX IF NOT EXISTS idx_argo_temp     
    ON argo_profiles(temperature);
