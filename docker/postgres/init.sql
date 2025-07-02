-- PostgreSQL initialization script for Meiyume AI Assistant

-- Create development database
CREATE DATABASE meiyume_ai_assistant_dev;

-- Create production database
SELECT 'CREATE DATABASE meiyume_ai_assistant_prod'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'meiyume_ai_assistant_prod')\gexec

-- Grant privileges to meiyume_user
GRANT ALL PRIVILEGES ON DATABASE meiyume_ai_assistant_dev TO meiyume_user;
GRANT ALL PRIVILEGES ON DATABASE meiyume_ai_assistant_prod TO meiyume_user;

-- Connect to development database and create extensions
\c meiyume_ai_assistant_dev;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Connect to production database and create extensions
\c meiyume_ai_assistant_prod;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; 