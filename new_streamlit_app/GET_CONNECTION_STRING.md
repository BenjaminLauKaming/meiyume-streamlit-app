# How to Get Your Supabase Connection String

## Step-by-Step Instructions:

### 1. Go to Your Supabase Dashboard
Visit: https://supabase.com/dashboard/project/xswknojsvovbzhcpgizw

### 2. Navigate to Database Settings
- Click on **Settings** (gear icon) in the left sidebar
- Click on **Database**

### 3. Find the Connection String
Look for one of these sections:
- **Connection string** (Uri) 
- **Connection pooling** → **Connection string**

### 4. Copy the URI
It should be in this format (replace [PASSWORD] with your actual password):

**Direct connection:**
```
postgresql://postgres:[PASSWORD]@db.xswknojsvovbzhcpgizw.supabase.co:5432/postgres
```

**Or connection pooler (recommended):**
```
postgresql://postgres.xswknojsvovbzhcpgizw:[PASSWORD]@[POOLER-HOST].supabase.co:6543/postgres
```

### 5. Update the .env File
Paste the EXACT connection string from your Supabase dashboard into the .env file.

### Important Notes:
- Use the **exact** format from Supabase dashboard
- Don't manually construct it
- Copy and paste directly from Supabase
- Make sure password is correct
