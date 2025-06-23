-- PostgreSQL initialization script for CAD Analyzer

-- Create development database
CREATE DATABASE cad_analyzer_dev;

-- Create production database (if not exists)
SELECT 'CREATE DATABASE cad_analyzer_prod'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'cad_analyzer_prod')\gexec

-- Grant all privileges to the user
GRANT ALL PRIVILEGES ON DATABASE cad_analyzer_dev TO cad_user;
GRANT ALL PRIVILEGES ON DATABASE cad_analyzer_prod TO cad_user;

-- Create extensions if needed
\c cad_analyzer_dev;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c cad_analyzer_prod;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Switch back to default database
\c postgres; 