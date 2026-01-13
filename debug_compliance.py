import os
import base64
import pandas as pd
from io import StringIO
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found.")
    exit(1)

engine = create_engine(DATABASE_URL)

def debug_latest_session():
    print("Fetching LATEST session...")
    query = text("""
        SELECT session_id, data FROM results 
        WHERE agent_type = 'com' 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    try:
        with engine.connect() as connection:
            result = connection.execute(query).fetchone()
            
            if not result:
                print("No data found.")
                return

            session_id = result[0]
            data = result[1]
            print(f"Latest Session ID: {session_id}")
            print("\n--- Root Data Structure ---")
            print(json.dumps(data, indent=2, default=str)[:1000] + "...")

            # Helper to find string in complex structure
            def find_b64(d):
                if isinstance(d, dict):
                    if "data" in d:
                        val = d["data"]
                        if isinstance(val, str) and len(val) > 100:
                            return val
                        return find_b64(val)
                elif isinstance(d, list):
                    if len(d) > 0:
                        return find_b64(d[0])
                return None

            csv_data = find_b64(data)
            
            if not csv_data:
                print("Could not find base64 string in structure.")
                return

            print(f"\nFound potential Base64 data (len={len(csv_data)})")
            
            # Decode CSV
            try:
                decoded_csv = base64.b64decode(csv_data).decode('utf-8')
                print("\n--- Decoded CSV Content (First 500 chars) ---")
                print(decoded_csv[:500])
                print("...\n------------------------------------------")
                
                df = pd.read_csv(StringIO(decoded_csv))
                
                # Sanitize column names
                df.columns = df.columns.str.strip()
                
                print("\n--- Pandas DataFrame Head ---")
                print(df.head())
                print(f"\nColumns: {df.columns.tolist()}")

            except Exception as e:
                print(f"Error decoding/parsing CSV: {e}")

    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    debug_latest_session()
