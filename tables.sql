-- 1. ENUM for user roles
CREATE TYPE user_role AS ENUM ('Customer', 'SystemAdmin', 'CompanyAdmin');

-- 2. Companies table
CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    admin_user_id INTEGER UNIQUE,
    CONSTRAINT admin_user_fk FOREIGN KEY (admin_user_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);

-- 3. Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(120) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    phone_number VARCHAR(20),
    profile_picture VARCHAR(255),
    spendable_points INTEGER DEFAULT 0,
    cumulative_points INTEGER DEFAULT 0,
    streak_count INTEGER DEFAULT 0,
    last_streak_timestamp TIMESTAMP,
    role user_role NOT NULL DEFAULT 'Customer',
    company_id INTEGER,
    CONSTRAINT user_company_fk FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE SET NULL
);


-- 4. ENUMs for activity
CREATE TYPE activity_type_enum AS ENUM ('water', 'steps', 'exercise', 'sleep');
CREATE TYPE unit_enum AS ENUM ('oz', 'steps', 'miles', 'hours', 'minutes', 'km');
CREATE TYPE exercise_type_enum AS ENUM ('yoga', 'run', 'cycling', 'strength', 'other');

-- 5. Activity logs
CREATE TABLE activity_log (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    activity_type activity_type_enum NOT NULL,
    value NUMERIC NOT NULL,
    unit unit_enum,
    exercise_type exercise_type_enum,
    proof BOOLEAN DEFAULT FALSE,
    proof_valid BOOLEAN DEFAULT NULL,
    proof_url VARCHAR(255),
    logged_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT activitylog_user_fk FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- 6. Vouchers table
CREATE TABLE vouchers (
    voucher_id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    cost_in_points INTEGER NOT NULL,
    available_quantity INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    company_id INTEGER,
    CONSTRAINT voucher_company_fk FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE CASCADE
);

-- 7. User Vouchers table
CREATE TABLE user_vouchers (
    user_voucher_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    voucher_id INTEGER NOT NULL,
    redeemed BOOLEAN DEFAULT FALSE,
    redeemed_at TIMESTAMP WITHOUT TIME ZONE,
    acquired_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT user_voucher_user_fk FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT user_voucher_voucher_fk FOREIGN KEY (voucher_id)
        REFERENCES vouchers(voucher_id)
        ON DELETE CASCADE
);

-- 8. Reminders Table
CREATE TABLE reminders (
    reminder_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    reminder_time TIMESTAMP NOT NULL,
    description VARCHAR(149) NOT NULL,
    send_sms BOOLEAN DEFAULT FALSE,
    is_sent BOOLEAN DEFAULT FALSE,
    is_completed BOOLEAN DEFAULT FALSE,
    CONSTRAINT reminders_user_fk FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

