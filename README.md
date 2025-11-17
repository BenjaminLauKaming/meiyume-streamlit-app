# Meiyume AI Assistant

Multi-purpose AI assistant application with Streamlit interface for CAD analysis, compliance checking, and quality control.

## Features

- **CAD Analysis**: Advanced 2D CAD drawing analysis with AI
- **Compliance Checker**: MSDS document compliance verification
- **Quality RAG Chat**: AI-powered quality control chat interface

## Architecture

```
Streamlit App → n8n Workflow → Supabase Database → Streamlit App (polls for results)
```

### How It Works

1. User uploads a file in Streamlit
2. File is sent to n8n workflow for processing
3. n8n processes the file and writes results directly to Supabase
4. Streamlit polls Supabase for results and displays them

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Supabase Connection

Create a `.env` file in the project root:

```env
# Supabase Database Configuration
# Get these values from your Supabase project dashboard: https://app.supabase.com

# Supabase Database Connection URL
# Format: postgresql://postgres.{ref}:{password}@aws-0-{region}.pooler.supabase.com:6543/postgres
# You can find this in: Project Settings > Database > Connection Pooling (Session mode)
# Or use the connection string from: Project Settings > Database > Connection String (URI)
DATABASE_URL=postgresql://postgres.{ref}:{your_password}@aws-0-{region}.pooler.supabase.com:6543/postgres

# Alternatively, you can use direct connection string (not recommended for production)
# Format: postgresql://postgres:{password}@{host}:5432/postgres
# DATABASE_URL=postgresql://postgres:your_password@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
```

Get your connection string from: https://app.supabase.com
Go to: Project Settings > Database > Connection Pooling (Session mode)

### 3. Run the Application

```bash
streamlit run main.py
```

## Database Tables

The application automatically creates a `results` table in Supabase with the following structure:

- `session_id` (VARCHAR, primary key)
- `agent_type` (VARCHAR, primary key) - values: 'cad', 'com' (compliance)
- `data` (JSONB) - contains the analysis results
- `created_at` (TIMESTAMP) - auto-updated timestamp

## n8n Workflow Setup

Your n8n workflows should end with a SQL node that inserts data into Supabase:

```sql
INSERT INTO results (session_id, agent_type, data)
VALUES (
    '{{ $json.session_id }}',
    'cad',  -- or 'com' for compliance
    '{{ JSON.stringify($json) }}'::jsonb
)
ON CONFLICT (session_id, agent_type)
DO UPDATE SET 
    data = EXCLUDED.data,
    created_at = NOW();
```

## Project Structure

```
.
├── main.py                      # Main application entry point
├── engAssistant.py              # CAD analysis module
├── complianceAssistant.py       # Compliance checker module
├── qualityRagChat.py           # Quality RAG chat module
├── requirements.txt             # Python dependencies
├── .env                         # Supabase credentials (create this - see Setup)
└── README.md                    # This file
```

## Requirements

- Python 3.9+
- Supabase account
- n8n workflows configured

## Version

5.0.0 (Supabase)

## License

Proprietary - Meiyume AI
