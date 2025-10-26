# Supabase Setup Guide

This application has been migrated from Docker to use Supabase as the database backend.

## What You Need to Provide

To connect your application to Supabase, you need to provide:

### 1. **Supabase Database URL** (Connection String)

You'll get this from your Supabase project dashboard.

#### How to Get Your Connection String:

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Select or create a project
3. Navigate to **Project Settings** (gear icon in the sidebar)
4. Click on **Database** in the settings menu
5. Scroll to **Connection Pooling** section
6. Copy the **Session mode** connection string, which looks like:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```

Alternatively, you can use the direct connection string from the **Connection String** section (URI format):
```
postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

> **Note:** The connection pooling URL (port 6543) is recommended for production as it's more efficient and handles connection limits better.

### 2. **Create Your .env File**

1. Create a file named `.env` in the project root directory
2. Add your Supabase connection string:

   ```env
   # Supabase Database Connection
   DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   
   # Webhook URL (for n8n callbacks)
   # Set this to your public URL or ngrok URL if testing locally
   WEBHOOK_URL=http://localhost:5001
   ```

3. Replace the placeholders with your actual values:
   - `[PROJECT-REF]`: Your project reference (found in Supabase dashboard)
   - `[YOUR-PASSWORD]`: Your database password
   - `[REGION]`: Your database region (e.g., `ap-southeast-1`)

### 3. **Example .env File**

Here's a complete example:

```env
# Supabase Database Connection
DATABASE_URL=postgresql://postgres.abc123def456:MySecurePassword123@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres

# Webhook URL for n8n callbacks
WEBHOOK_URL=https://your-ngrok-url.ngrok.io
```

## Running the Application

### Local Development:

1. Make sure you have created the `.env` file with your Supabase credentials
2. Install dependencies (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   streamlit run main.py
   ```

### Database Table Creation

The application will automatically create the required `results` table in your Supabase database on first run. No manual setup required!

## What Changed?

### Removed:
- ✅ `docker-compose.yml` - Docker orchestration file
- ✅ `Dockerfile` - Docker container build file
- ✅ All Docker-related setup instructions

### Added:
- ✅ `.env` file for environment configuration
- ✅ `env.example` - Template for environment variables
- ✅ Python-dotenv support for loading environment variables
- ✅ Better error messages for missing database configuration

### Updated:
- ✅ `main.py` - Now uses `.env` file instead of Docker environment variables
- ✅ Database connection now points to Supabase
- ✅ Error messages updated to reference Supabase instead of Docker
- ✅ Setup instructions updated in the application sidebar

## Testing Your Connection

Once you've set up your `.env` file, you can test the connection by:

1. Running the application: `streamlit run main.py`
2. The app will automatically verify the database connection
3. If successful, you'll see the application interface
4. If there are issues, you'll see specific error messages guiding you to fix them

## Troubleshooting

### "Database connection failed"

- Double-check your `.env` file exists and contains the correct `DATABASE_URL`
- Verify your database password is correct
- Ensure your Supabase project is active
- Check that you're using the correct connection string format

### "DATABASE_URL environment variable not set"

- Make sure you've created a `.env` file in the project root
- Verify the file contains the `DATABASE_URL` variable
- Restart the application after creating/modifying the `.env` file

### Connection timeout issues

- Try using the connection pooling URL (port 6543) instead of direct connection
- Check if your IP address needs to be whitelisted in Supabase security settings
- Verify your network allows outbound connections to Supabase

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Database Connection Guide](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Environment Variables Best Practices](https://12factor.net/config)

## Need Help?

If you encounter any issues, check:
1. Your `.env` file is properly formatted
2. Your Supabase database is running and accessible
3. All required packages are installed: `pip install -r requirements.txt`
