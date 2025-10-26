# Application Architecture

## New Architecture (Supabase)

### Flow Diagram
```
Streamlit App → n8n Workflow → Supabase Database → Streamlit App (polls for results)
```

### How It Works

1. **User submits file** in Streamlit (CAD, ESG, or Compliance analysis)
2. **Streamlit sends** file to n8n webhook
3. **n8n processes** the file (AI analysis, data extraction, etc.)
4. **n8n writes directly** to Supabase database via SQL node
5. **Streamlit polls** Supabase for results and displays them

### Key Changes from Old Architecture

#### Removed (No Longer Needed):
- ❌ Flask webhook server (port 5001)
- ❌ Webhook callbacks from n8n to Streamlit
- ❌ Docker setup
- ❌ ngrok for local development (no longer needed for webhooks)

#### New/Updated:
- ✅ n8n writes directly to Supabase with SQL node
- ✅ Streamlit polls Supabase for results
- ✅ Simpler architecture - one less moving part
- ✅ No need for public URLs (like ngrok)
- ✅ Direct database integration

### n8n Workflow SQL Node

Your n8n workflow should end with a SQL node that inserts data:

```sql
INSERT INTO results (session_id, agent_type, data)
VALUES (
    '{{ $json.session_id }}',
    'cad',  -- or 'esg', 'compliance', etc.
    '{{ JSON.stringify($json) }}'::jsonb
)
ON CONFLICT (session_id, agent_type)
DO UPDATE SET 
    data = EXCLUDED.data,
    created_at = NOW();
```

### Database Table

The `results` table is automatically created when you run the app. Structure:

- `session_id` (VARCHAR, primary key)
- `agent_type` (VARCHAR, primary key) - values: 'cad', 'esg', 'compliance'
- `data` (JSONB) - contains the analysis results
- `created_at` (TIMESTAMP) - auto-updated

### Running the Application

1. Make sure your `.env` file exists with Supabase credentials
2. Run: `streamlit run main.py`
3. The app will:
   - Connect to Supabase
   - Create the `results` table if it doesn't exist
   - Start polling for results

No ngrok or Docker needed anymore! 🎉
