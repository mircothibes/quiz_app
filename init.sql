-- init.sql
-- This script runs automatically when PostgreSQL container starts for the first time

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- Questions Table
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    correct_answer VARCHAR(1) NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL
);

-- Insert Sample Categories
INSERT INTO categories (name, description) VALUES 
('Python Basics', 'Fundamental Python programming concepts'),
('SQL & Databases', 'Database queries and design'),
('Docker', 'Containerization and deployment')
ON CONFLICT (name) DO NOTHING;

-- Insert Sample Questions
INSERT INTO questions (category_id, question_text, correct_answer, option_a, option_b, option_c, option_d) 
VALUES
(1, 'What is the output of: print(2 ** 3)?', 'B', '6', '8', '9', '5'),
(1, 'Which keyword defines a function in Python?', 'C', 'function', 'func', 'def', 'define'),
(2, 'Which SQL command retrieves data?', 'A', 'SELECT', 'GET', 'FETCH', 'RETRIEVE'),
(3, 'What command starts a Docker container?', 'D', 'docker start', 'docker begin', 'docker init', 'docker run')
ON CONFLICT DO NOTHING;

-- Create a test user (password: "test123")
INSERT INTO users (username, password_hash) VALUES 
('demo', 'test123')
ON CONFLICT (username) DO NOTHI
