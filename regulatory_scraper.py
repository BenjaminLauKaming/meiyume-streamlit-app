import streamlit as st
import requests
from bs4 import BeautifulSoup
import io
import csv
import json
import re
import pandas as pd
from sqlalchemy import text

def scrape_annex(annex_id):
    """
    Scrapes Annex II or III from EUR-Lex with dynamic version discovery.
    annex_id: 'II' or 'III'
    """
    entry_url = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02009R1223-20250901"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # 1. Get the entry page to find the latest version link
    resp = requests.get(entry_url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # 2. Find the latest version from #consLegVersions nav
    # The user suggested matching the first li a in that nav
    latest_version_link = None
    cons_nav = soup.select_one("#consLegVersions nav.consLegNav ul li:first-child a")
    if cons_nav:
        latest_version_link = cons_nav["href"]
        
    if not latest_version_link:
        # Fallback to any link that looks like a version link in that area
        cons_nav_any = soup.select_one("#consLegVersions a[data-celex]")
        if cons_nav_any:
            latest_version_link = cons_nav_any["href"]
            
    url = latest_version_link if latest_version_link else entry_url
    if not url.startswith("http"):
        url = "https://eur-lex.europa.eu" + url.replace("./", "/").replace("../", "/")
        
    # 3. Go to the version page and find the HTML EN link
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    html_en_link = None
    target = soup.find("td", id="format_language_table_HTML_EN")
    if target:
        a = target.find("a")
        if a:
            html_en_link = a["href"]
            
    if not html_en_link:
        # Final fallback search on the page for HTML and LNG=EN
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            if "HTML" in href and "LNG=EN" in href.upper():
                html_en_link = href
                break
                
    doc_url = html_en_link if html_en_link else url
    if not doc_url.startswith("http"):
        doc_url = "https://eur-lex.europa.eu" + doc_url.replace("./", "/").replace("../", "/")
        
    # 4. Fetch actual document
    resp = requests.get(doc_url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    selector = f"#anx_{annex_id} > div > table > tbody"
    tbody = soup.select_one(selector)
    if not tbody:
        # Fallback for different structures
        tbody = soup.select_one(f"#anx_{annex_id} table tbody") or soup.select_one(f"#anx_{annex_id} table")
        
    if not tbody:
        raise ValueError(f"Table body for Annex {annex_id} not found at {doc_url}!")

    tr_all = tbody.find_all("tr")
    max_cols = 5 if annex_id == "II" else 9
    pending = {}  # col_idx -> (text, remaining_rows)
    rows = []
    
    skip_first = 3 if annex_id == "II" else 4
    skipped = 0

    for tr in tr_all:
        # 1. Identify row type (discard modifiers but keep them for rowspan countdown)
        is_mod = (tr.find("a", href=True) and any(m in tr.get_text() for m in ["▼M", "▼C", "▼"])) or not tr.find_all(["td", "th"])
        
        cells = [None] * max_cols
        
        # 2. Fill cells already reserved by previous rowspans
        new_pending = {}
        for c_idx, (txt, remain) in pending.items():
            if c_idx < max_cols:
                cells[c_idx] = txt
                if remain > 1:
                    new_pending[c_idx] = (txt, remain - 1)
        pending = new_pending
        
        # 3. Process current physical row's TDs
        available_col = 0
        for td in tr.find_all(["td", "th"]):
            # Find next empty column slot
            while available_col < max_cols and cells[available_col] is not None:
                available_col += 1
            
            if available_col >= max_cols:
                break
                
            # Extract content
            paragraphs = td.find_all("p")
            if not paragraphs:
                text = td.get_text(strip=True)
            else:
                text = " ".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            text = re.sub(r'\[\d+\]', '', text).strip()
            rowspan = int(td.get("rowspan") or 1)
            colspan = int(td.get("colspan") or 1)
            
            # Fill cells and set pending for rowspan
            for i in range(colspan):
                current_c = available_col + i
                if current_c < max_cols:
                    cells[current_c] = text
                    if rowspan > 1:
                        pending[current_c] = (text, rowspan - 1)
            
            available_col += colspan

        # 4. Finalize row cells (fill None with empty)
        final_row = [c if c is not None else "" for c in cells]

        # 5. Skip headers and modification rows
        if skipped < skip_first:
            skipped += 1
            continue
            
        if not is_mod and any(final_row):
            rows.append(final_row)

    merged_rows = []
    current_entry = None

    for r in rows:
        index_val = r[0].strip()
        is_new_index = index_val and re.search(r'\d+', index_val)
        
        if is_new_index:
            if current_entry and current_entry[0] == index_val:
                for i in range(1, max_cols):
                    new_val = r[i].strip()
                    if new_val and new_val not in current_entry[i]:
                        current_entry[i] = (current_entry[i] + " " + new_val).strip()
            else:
                if current_entry:
                    merged_rows.append(current_entry)
                current_entry = list(r)
        else:
            if current_entry:
                for i in range(1, max_cols):
                    new_val = r[i].strip()
                    if new_val and new_val not in current_entry[i]:
                        current_entry[i] = (current_entry[i] + " " + new_val).strip()
            else:
                current_entry = list(r)

    if current_entry:
        merged_rows.append(current_entry)

    rows_mapped = []
    for r in merged_rows:
        if annex_id == "II":
            name = r[1]
            cas_raw = r[2]
            ec = r[3]
            cond = r[4]
            classification = "Prohibited"
            limits_parts = [f"Index: {r[0]}"] if r[0] else []
            if ec: limits_parts.append(f"EC: {ec}")
            if cond: limits_parts.append(cond)
            limits = "; ".join(limits_parts)
        else:
            name = f"{r[1]} / {r[2]}".strip(" /")
            cas_raw = r[3]
            ec = r[4]
            classification = "Restricted"
            limits_parts = [f"Ref: {r[0]}"] if r[0] else []
            if ec: limits_parts.append(f"EC: {ec}")
            if r[5]: limits_parts.append(f"Scope: {r[5]}")
            if r[6]: limits_parts.append(f"Max: {r[6]}")
            if r[7]: limits_parts.append(f"Other: {r[7]}")
            if r[8]: limits_parts.append(f"Warnings: {r[8]}")
            limits = "; ".join(limits_parts)

        # Robust CAS splitting: handle space, comma, semicolon, slash, en-dash, em-dash
        cas_clean = re.sub(r'\(.*?\)', '', cas_raw)
        # Split by various delimiters including en-dash (\u2013) and em-dash (\u2014)
        cas_list = [c.strip() for c in re.split(r'[;,\s/\u2013\u2014]+', cas_clean) if c.strip()]
        # Filter: Must contain digits to avoid purely non-numeric junk
        cas_list = [c for c in cas_list if any(char.isdigit() for char in c)]
        cas_list = list(dict.fromkeys(cas_list))
        cas_json = json.dumps({"cas": cas_list})
        
        rows_mapped.append([name, cas_json, classification, limits])

    output = io.StringIO()
    writer = csv.writer(output)
    target_headers = ["chemical_name", "cas_no", "classification", "limits"]
    writer.writerow(target_headers)
    writer.writerows(rows_mapped)
    return output.getvalue()

def scrape_table_3_clp():
    """
    Scrapes Table 3 CLP dynamically by finding the latest version from EUR-Lex.
    """
    entry_url = "https://eur-lex.europa.eu/eli/reg/2008/1272/oj/eng"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # 1. Go to entry page
    resp = requests.get(entry_url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # 2. Find Latest Version / HTML EN link
    # Try the user's suggested area first
    html_en_link = None
    
    # Search for links in #documentView as suggested
    doc_view = soup.select_one("#documentView")
    if doc_view:
        # User suggested //*[@id="documentView"]/div/div/div[4]/div/a
        # We'll look for any link that looks like a consolidated version (containing AUTO or dates)
        links = doc_view.find_all("a", href=True)
        for link in links:
            href = link["href"]
            if "AUTO" in href or re.search(r'\d{8}', href):
                html_en_link = href
                break

    if not html_en_link:
        # Fallback to the language table
        target = soup.find("td", id="format_language_table_HTML_EN")
        if target:
            a = target.find("a")
            if a:
                html_en_link = a["href"]
    
    if not html_en_link:
        # Final fallback search
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            if "AUTO" in href or ("HTML" in href and "LNG=EN" in href.upper()):
                html_en_link = href
                break
                
    url = html_en_link if html_en_link else entry_url
    if url and not url.startswith("http"):
        url = "https://eur-lex.europa.eu" + url.replace("./", "/").replace("../", "/")
        
    # 3. Handle potential size warning / redirection
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Check for both #documentView and #errorDocumentView size warnings
    # The warning usually has a link with "Click here to view it"
    warning_link = None
    warning_tag = soup.select_one(".alert-warning a, #errorDocumentView a, #documentView .alert a")
    if warning_tag and "click here" in warning_tag.get_text().lower():
        warning_link = warning_tag["href"]
        
    if warning_link:
        url = warning_link
        if not url.startswith("http"):
            url = "https://eur-lex.europa.eu" + url.replace("./", "/").replace("../", "/")
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

    # Now we have the final document 'soup' - continue with optimized parsing
    # 4. Look for all 'Table 3' labels in the document
    labels = soup.find_all(string=re.compile(r"^Table 3$"))
    tbody = None
    
    for label in labels:
        # Table 3 is typically in a <p> or <span>. Find the next table in the DOM.
        table = label.find_next("table")
        if table:
            # Verify this is the correct table (Index No must be in the header area)
            header_text = table.get_text()
            if "Index No" in header_text and "Chemical name" in header_text:
                tbody = table.find("tbody")
                if tbody:
                    break
    
    # Fallback: search all tables if label-based find fails
    if not tbody:
        for table in soup.find_all("table"):
            text = table.get_text()
            if "Index No" in text and "Chemical name" in text and "Classification" in text:
                tbody = table.find("tbody")
                if tbody:
                    break
    
    if not tbody:
        raise ValueError("Table 3 CLP not found! The document structure might have changed at " + url)

    target_headers = ["chemical_name", "cas_no", "classification", "limits"]
    
    rows = tbody.find_all("tr")
    csv_data = []
    
    # Identify how many header rows to skip (look for actual data rows)
    # The original headers had 11 columns
    skip_rows = 0
    for i, row in enumerate(rows):
        cells = row.find_all(["td", "th"])
        if len(cells) == 11:
            # Check if first cell looks like an Index No (digits or ranges)
            first_cell_text = cells[0].get_text(strip=True)
            if re.search(r'\d+', first_cell_text):
                skip_rows = i
                break
    
    for row in rows[skip_rows:]:
        cells = row.find_all(["td", "th"])
        
        # Handle special metadata rows (colspan="11")
        if len(cells) == 1 and cells[0].get("colspan") == "11":
            continue
            
        if len(cells) != 11:
            continue

        # Map according to the user's requirement:
        # chemical_name = col 1
        # cas_no = col 3
        # classification = col 4
        # Limits = col 9
        
        row_values = {}
        for idx in [1, 3, 4, 9]:
            cell = cells[idx]
            paragraphs = cell.find_all("p")
            if not paragraphs:
                cell_texts = [cell.get_text(strip=True)]
            else:
                cell_texts = [
                    "" if p.get_text().strip() in ["—", "-"] 
                    else re.sub(r'\[\d+\]', '', p.get_text().strip()).strip().replace('"', '""') 
                    for p in paragraphs if p.get_text().strip()
                ]
            
            # Formulate the value
            if idx == 3: # cas_no: always store as clean array for SQL compatibility
                # Clean each element (strip [n] and parentheses like (HCl)) and filter empty
                cas_list = []
                for c in cell_texts:
                    if not c.strip(): continue
                    c_clean = re.sub(r'\[\d+\]', '', c)
                    c_clean = re.sub(r'\(.*?\)', '', c_clean).strip()
                    cas_list.append(c_clean)
                
                # Split any internal spaces if paragraphs were joined messy
                final_cas = []
                for c in cas_list:
                    final_cas.extend([x.strip() for x in re.split(r'[;,\s/]+', c) if x.strip()])
                
                # Remove duplicates and filter for digit-containing strings
                final_cas = [x for x in list(dict.fromkeys(final_cas)) if any(char.isdigit() for char in x)]
                row_values['cas_no'] = json.dumps({"cas": final_cas})
            elif idx == 1:
                row_values['chemical_name'] = " ".join(cell_texts) if cell_texts else ""
            elif idx == 4:
                row_values['classification'] = " ".join(cell_texts) if cell_texts else ""
            elif idx == 9:
                row_values['limits'] = " ".join(cell_texts) if cell_texts else ""
                
        csv_data.append([
            row_values.get('chemical_name', ''),
            row_values.get('cas_no', ''),
            row_values.get('classification', ''),
            row_values.get('limits', '')
        ])


    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(target_headers)
    writer.writerows(csv_data)
    return output.getvalue()

def sync_csv_to_db(table_name, csv_data, engine):
    """
    Clears the specified table and imports the new CSV data.
    Automatically adds missing columns to the database if they exist in the CSV.
    Returns (success, message).
    """
    try:
        df = pd.read_csv(io.StringIO(csv_data))
        # Ensure 'created_at' is not in the CSV data to let the DB handle it
        if 'created_at' in df.columns:
            df = df.drop(columns=['created_at'])
            
        with engine.begin() as conn:
            # PROACTIVE SCHEMA FIX: Ensure all CSV columns exist in the DB
            for col in df.columns:
                try:
                    conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS "{col}" TEXT;'))
                except Exception as alter_e:
                    print(f"Schema update skipped for {table_name}.{col}: {alter_e}")

            # Clear existing data
            conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;"))
            
            # Insert new data
            df.to_sql(table_name, conn, if_exists='append', index=False)
        return True, "Success"
    except Exception as e:
        error_msg = str(e)
        print(f"Sync error for {table_name}: {error_msg}")
        return False, error_msg

def init_regulatory_db(engine):
    """Creates the specific tables for the regulatory scrapers."""
    queries = [
        "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";",
        """
        CREATE TABLE IF NOT EXISTS cmr (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            chemical_name TEXT,
            cas_no TEXT,
            classification TEXT,
            limits TEXT,
            created_at DATE DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS cosmetic_annex2 (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            chemical_name TEXT,
            cas_no TEXT,
            classification TEXT,
            limits TEXT,
            created_at DATE DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS cosmetic_annex3 (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            chemical_name TEXT,
            cas_no TEXT,
            classification TEXT,
            limits TEXT,
            created_at DATE DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS svhc (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            chemical_name TEXT,
            cas_no text,
            classification TEXT,
            limits TEXT,
            isDelisted BOOLEAN DEFAULT NULL,
            created_at DATE DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS prop65 (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            chemical_name TEXT,
            cas_no text,
            classification TEXT,
            limits TEXT,  
            created_at DATE DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS pfas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            chemical_name TEXT,
            cas_no text,
            classification text,
            limits TEXT,
            created_at DATE DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS loreal (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            chemical_name TEXT,
            cas_no text,
            created_at DATE DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS customer_lists (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            table_name TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            created_at DATE DEFAULT NOW()
        );
        """,
        # Ensure existing tables get the new columns if they were created earlier
        "ALTER TABLE prop65 ADD COLUMN IF NOT EXISTS classification TEXT;",
        "ALTER TABLE prop65 ADD COLUMN IF NOT EXISTS limits TEXT;",
        "ALTER TABLE svhc ADD COLUMN IF NOT EXISTS classification TEXT;",
        "ALTER TABLE svhc ADD COLUMN IF NOT EXISTS limits TEXT;",
        "ALTER TABLE loreal ADD COLUMN IF NOT EXISTS classification TEXT;",
        "ALTER TABLE loreal ADD COLUMN IF NOT EXISTS limits TEXT;"
    ]
    try:
        # Using engine.begin() ensures immediate commit and cleaner transactions in SQLAlchemy 2.0
        with engine.begin() as conn:
            for query in queries:
                try:
                    conn.execute(text(query))
                except Exception as inner_e:
                    # Log but continue for pgcrypto if it fails (might be permission issue but already exists)
                    if "pgcrypto" in query:
                        print(f"Note: pgcrypto check skipped: {inner_e}")
                    else:
                        raise inner_e
        return True
    except Exception as e:
        print(f"Error initializing regulatory database: {e}")
        return False

def scrape_prop65(manual_url=None):
    """
    Scrapes the Proposition 65 list from OEHHA with dynamic link discovery,
    manual URL fallback, and specific CSV cleaning (skipping 11 rubbish rows).
    """
    base_url = "https://oehha.ca.gov/proposition-65/proposition-65-list"
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://oehha.ca.gov/proposition-65"
    }

    csv_link = manual_url

    if not csv_link:
        resp = session.get(base_url, headers=headers)
        # Check for block but don't raise immediately if we have a hardcoded fallback
        if "Incapsula" in resp.text and "incident_id" in resp.text:
            csv_link = None # Discovery failed due to block
        else:
            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.find_all("a", href=True)
            for link in links:
                href = link["href"].lower()
                title = (link.get("title") or "").lower()
                text = re.sub(r'\s+', ' ', link.get_text()).strip()
                if re.search(r'Proposition 65 List.*\(CSV\)', text, re.I):
                    csv_link = link["href"]
                    break
                if "p65chemicalslist.csv" in href or "p65chemicalslist.csv" in title:
                    csv_link = link["href"]
                    break
            
            if not csv_link:
                target_div = soup.select_one(".field--name-field-media-crnr-documents")
                if target_div:
                    a = target_div.find("a", href=True)
                    if a:
                        csv_link = a["href"]

    if not csv_link:
        # Final hardcoded fallback for the most recent known link
        csv_link = "https://oehha.ca.gov/sites/default/files/media/2025-01/p65chemicalslist.csv"

    if not csv_link.startswith("http"):
        csv_link = "https://oehha.ca.gov" + csv_link
        
    csv_resp = session.get(csv_link, headers=headers)
    csv_resp.raise_for_status()
    
    # 2. CSV Cleaning: Skip row 1 to 11 (rubbish). Row 12 is header.
    df = pd.read_csv(io.StringIO(csv_resp.text), skiprows=11)
    
    # 3. Column Mapping:
    target_df = pd.DataFrame()
    df.columns = [c.strip() for c in df.columns]
    
    if "Chemical" in df.columns:
        target_df['chemical_name'] = df["Chemical"]
    
    # Standardize CAS
    if "CAS No." in df.columns:
        def clean_cas(c):
            if pd.isna(c) or str(c).strip().lower() in ["nan", "", "-"]:
                return json.dumps({"cas": []})
            c_str = str(c)
            # Remove parentheses content and clean markers
            c_clean = re.sub(r'\(.*?\)', '', c_str)
            c_clean = re.sub(r'\[\d+\]', '', c_clean).strip()
            # Split by various delimiters
            cas_list = [x.strip() for x in re.split(r'[;,\s/\u2013\u2014]+', c_clean) if x.strip()]
            # Keep only segments with digits
            cas_list = [x for x in list(dict.fromkeys(cas_list)) if any(char.isdigit() for char in x)]
            return json.dumps({"cas": cas_list})
        target_df['cas_no'] = df["CAS No."].apply(clean_cas)
    else:
        target_df['cas_no'] = json.dumps({"cas": []})

    target_df['classification'] = "Prop 65 Listed"
    
    # Limits (handle the NSRL/MADL column)
    # Using regex to find the column because of the special character in the user request
    limit_col = [c for c in df.columns if re.search(r'NSRL or MADL', c, re.I)]
    if limit_col:
        target_df['limits'] = df[limit_col[0]].apply(lambda x: str(x).strip() if pd.notna(x) else "")
    else:
        target_df['limits'] = ""
        
    return target_df[["chemical_name", "cas_no", "classification", "limits"]].to_csv(index=False)

def scrape_svhc():
    """
    Scrapes the REACH SVHC Candidate List from ECHA using their CSV export endpoint.
    Handles disclaimer cookies and dynamic form parameters.
    """
    url = "https://echa.europa.eu/candidate-list-table"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://echa.europa.eu/"
    }
    
    session = requests.Session()
    # 1. GET page to establish session and get dynamic parameters
    resp = session.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Extract dynamic form date (timestamp)
    form_date = ""
    date_input = soup.find("input", {"name": re.compile(r"formDate")})
    if date_input:
        form_date = date_input.get("value", "")
        
    # Extract total count (to ensure we get all records)
    total_count = "253" # fallback
    total_input = soup.find("input", {"id": re.compile(r"totalRecs")})
    if total_input:
        total_count = total_input.get("value", "253")
    else:
        # Try to find it in the text if input is missing
        match = re.search(r'totalRecs\s*:\s*(\d+)', resp.text)
        if match:
            total_count = match.group(1)

    # 2. POST to the export endpoint
    export_url = "https://echa.europa.eu/candidate-list-table?p_p_id=disslists_WAR_disslistsportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=exportResults&p_p_cacheability=cacheLevelPage"
    
    data = {
        "_disslists_WAR_disslistsportlet_exportType": "csv",
        "_disslists_WAR_disslistsportlet_exportColumns": "name,ecNumber,casNumber,haz_detailed_concern,dte_inclusion,doc_cat_decision,doc_cat_iuclid_dossier,doc_cat_supdoc,doc_cat_rcom,prc_external_remarks",
        "_disslists_WAR_disslistsportlet_formDate": form_date,
        "_disslists_WAR_disslistsportlet_orderByCol": "dte_inclusion",
        "_disslists_WAR_disslistsportlet_orderByType": "desc",
        "_disslists_WAR_disslistsportlet_total": total_count
    }
    
    # We need to simulate the disclaimer acceptance by adding a cookie or performing a specific request if needed
    # Usually ECHA's disclaimer button sets a cookie like 'echadisclaimer=accepted' or similar
    # In my browser test, I clicked it. Let's try sending the POST directly first as many sessions hold it.
    
    csv_resp = session.post(export_url, headers=headers, data=data)
    csv_resp.raise_for_status()
    
    if "text/csv" not in csv_resp.headers.get("Content-Type", "").lower():
        # Might be redirected to disclaimer page again
        re_disclaim_url = "https://echa.europa.eu/candidate-list-table?_disslists_WAR_disslistsportlet_disclaimerAccepted=true"
        session.get(re_disclaim_url, headers=headers)
        csv_resp = session.post(export_url, headers=headers, data=data)
        csv_resp.raise_for_status()

    # 3. Standardize Output
    # The ECHA CSV has 12 lines of preamble.
    csv_text = csv_resp.text
    lines = csv_text.splitlines()
    
    # Find where the actual data starts (the header row starting with "Substance name")
    start_idx = 0
    for i, line in enumerate(lines):
        if "Substance name" in line:
            start_idx = i
            break
            
    # Re-read with pandas skipping the preamble
    # ECHA often uses tab-separated even if the extension is .csv
    try:
        echa_df = pd.read_csv(io.StringIO("\n".join(lines[start_idx:])), sep=None, engine='python')
    except Exception:
        # Fallback to tab if auto-detection fails
        echa_df = pd.read_csv(io.StringIO("\n".join(lines[start_idx:])), sep='\t')
    
    target_df = pd.DataFrame()
    # ECHA column names can be tricky, they usually have quotes and might have leading spaces
    echa_df.columns = [c.strip().replace('"', '') for c in echa_df.columns]
    
    # Map Columns accurately with case-insensitivity
    def find_col(keywords):
        for c in echa_df.columns:
            if any(k.lower() in str(c).lower() for k in keywords):
                return c
        return None

    name_col = find_col(["Substance", "Name"])
    ec_col = find_col(["EC No", "ecNumber", "EC"])
    cas_col = find_col(["CAS No", "casNumber", "CAS"])
    reason_col = find_col(["Reason", "haz_detailed", "Concern"])
    date_col = find_col(["Inclusion", "dte_inclusion", "Date"])
    
    # Check if we found essential columns
    if not (name_col and cas_col):
        raise ValueError(f"Could not find essential columns (Name, CAS) in CSV. Found: {list(echa_df.columns)}")

    target_df['chemical_name'] = echa_df[name_col]
    
    # Standardize CAS to JSON array
    def clean_cas(c):
        if pd.isna(c) or str(c).strip().lower() in ["nan", "", "-", "n/a"]:
            return json.dumps({"cas": []})
        c_str = str(c).strip()
        # SVHC CAS are usually clean, but let's be safe
        cas_list = [x.strip() for x in re.split(r'[;,\s/]+', c_str) if x.strip()]
        # Filter for valid CAS-like strings (contains digits)
        cas_list = [x for x in cas_list if any(char.isdigit() for char in x)]
        return json.dumps({"cas": sorted(list(set(cas_list)))})
    
    target_df['cas_no'] = echa_df[cas_col].apply(clean_cas)
    target_df['classification'] = "SVHC"
    
    # Consolidation for limits field
    def format_limits(r):
        parts = []
        if ec_col and pd.notna(r[ec_col]) and str(r[ec_col]).strip() not in ["-", ""]:
            parts.append(f"EC: {r[ec_col]}")
        if date_col and pd.notna(r[date_col]) and str(r[date_col]).strip() not in ["-", ""]:
            parts.append(f"Date: {r[date_col]}")
        if reason_col and pd.notna(r[reason_col]) and str(r[reason_col]).strip() not in ["-", ""]:
            parts.append(f"Reason: {r[reason_col]}")
        return "; ".join(parts)

    target_df['limits'] = echa_df.apply(format_limits, axis=1)

    return target_df[["chemical_name", "cas_no", "classification", "limits"]].to_csv(index=False)


# --- Customer List Management Functions ---

def get_customer_lists(engine):
    """Returns list of registered customer tables as [(table_name, display_name), ...]"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT table_name, display_name FROM customer_lists ORDER BY display_name"))
            return [(row[0], row[1]) for row in result]
    except Exception as e:
        print(f"Error fetching customer lists: {e}")
        return []

def add_customer_list(engine, table_name, display_name):
    """Register a new customer list and create its table."""
    table_name = re.sub(r'[^a-z0-9_]', '_', table_name.lower().strip())
    try:
        with engine.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    chemical_name TEXT,
                    cas_no TEXT,
                    classification TEXT,
                    limits TEXT,
                    created_at DATE DEFAULT NOW()
                );
            """))
            conn.execute(text(
                "INSERT INTO customer_lists (table_name, display_name) VALUES (:tn, :dn) ON CONFLICT (table_name) DO NOTHING"
            ), {"tn": table_name, "dn": display_name})
        return True, f"Created table '{table_name}'"
    except Exception as e:
        return False, str(e)

def _cas_json_to_plain(cas_json_str):
    """Convert DB format {"cas":["206-44-0"]} to plain '206-44-0' for user."""
    if not cas_json_str or pd.isna(cas_json_str):
        return ""
    try:
        parsed = json.loads(str(cas_json_str))
        if isinstance(parsed, dict) and "cas" in parsed:
            cas_list = parsed["cas"]
            if isinstance(cas_list, list):
                return ", ".join(cas_list)
            return str(cas_list)
    except (json.JSONDecodeError, TypeError):
        pass
    return str(cas_json_str)

def _cas_plain_to_json(cas_plain_str):
    """Convert user plain '206-44-0, 123-45-6' to DB format {"cas":["206-44-0","123-45-6"]}."""
    if not cas_plain_str or (isinstance(cas_plain_str, float) and pd.isna(cas_plain_str)):
        return json.dumps({"cas": []})
    cas_str = str(cas_plain_str).strip()
    if not cas_str:
        return json.dumps({"cas": []})
    cas_list = [c.strip() for c in re.split(r'[;,\s]+', cas_str) if c.strip()]
    cas_list = [c for c in cas_list if any(ch.isdigit() for ch in c)]
    cas_list = list(dict.fromkeys(cas_list))
    return json.dumps({"cas": cas_list})

def download_customer_list(engine, table_name):
    """Download a customer table from DB and return user-readable CSV bytes."""
    table_name = re.sub(r'[^a-z0-9_]', '_', table_name.lower().strip())
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT chemical_name, cas_no, classification, limits FROM {table_name}"))
            rows = result.fetchall()
        df = pd.DataFrame(rows, columns=["chemical_name", "cas_no", "classification", "limits"])
        df["cas_no"] = df["cas_no"].apply(_cas_json_to_plain)
        return df.to_csv(index=False)
    except Exception as e:
        raise ValueError(f"Failed to download '{table_name}': {e}")

def upload_customer_list(engine, table_name, uploaded_file):
    """Parse user-uploaded CSV/Excel, convert plain CAS to JSON, and sync to DB."""
    table_name = re.sub(r'[^a-z0-9_]', '_', table_name.lower().strip())
    try:
        filename = uploaded_file.name.lower()
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

        required = {"chemical_name", "cas_no"}
        missing = required - set(df.columns)
        if missing:
            return False, f"Missing required columns: {', '.join(missing)}. Expected: chemical_name, cas_no, classification, limits"

        if "classification" not in df.columns:
            df["classification"] = ""
        if "limits" not in df.columns:
            df["limits"] = ""

        df["cas_no"] = df["cas_no"].apply(_cas_plain_to_json)
        df = df.dropna(subset=["chemical_name"])
        df = df[df["chemical_name"].str.strip() != ""]
        df = df[["chemical_name", "cas_no", "classification", "limits"]]

        csv_data = df.to_csv(index=False)
        return sync_csv_to_db(table_name, csv_data, engine)
    except Exception as e:
        return False, str(e)


# --- Streamlit UI ---

def regulatory_scraper_page(engine):
    st.title("Regulatory Scraper")
    st.markdown("""
    Generate and download the latest data from European and International regulatory sources.
    All scrapers are optimized for speed and handle merged table cells automatically.
    """)
    # Database Management
    st.subheader("Database Setup")
    st.write("Click below to create or update the required tables in Supabase (`cmr`, `annex2`, `annex3`, `svhc`, `prop65`, etc.).")
    if st.button("Create & Sync Database Tables", use_container_width=True):
        with st.spinner("Synchronizing schema..."):
            if init_regulatory_db(engine):
                st.success("Successfully created/verified all tables: `cmr`, `annex2`, `annex3`, `svhc`, `prop65`.")
            else:
                st.error("Failed to synchronize database. Check logs.")

    st.link_button("Open Supabase Dashboard", "https://supabase.com/dashboard/project/ixsxmovayvtdeejdokvf", use_container_width=True)

    st.divider()

    # Scrapers
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("CMR CLC Regulation")
        st.info("Source: Publications Office of the EU (DOC_2 - Table 3)")
        if st.button("Scrape & Download", key="btn_clp"):
            with st.spinner("Extracting classification data..."):
                try:
                    csv_data = scrape_table_3_clp()
                    st.download_button(label="Download CSV", data=csv_data, file_name="cmr_clc_regulation.csv", mime="text/csv")
                    success, msg = sync_csv_to_db("cmr", csv_data, engine)
                    if success:
                        st.success("Extraction complete and Database synced!")
                    else:
                        st.error(f"Extraction complete, but Database sync failed: {msg}")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.subheader("Cosmetic Regulation CE annex II")
        st.info("Source: EUR-Lex (Annex II - Prohibited Substances)")
        if st.button("Scrape & Download", key="btn_annex2"):
            with st.spinner("Extracting Annex II..."):
                try:
                    csv_data = scrape_annex("II")
                    st.download_button(label="Download CSV", data=csv_data, file_name="annex_II.csv", mime="text/csv")
                    success, msg = sync_csv_to_db("cosmetic_annex2", csv_data, engine)
                    if success:
                        st.success("Extraction complete and Database synced!")
                    else:
                        st.error(f"Extraction complete, but Database sync failed: {msg}")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.subheader("Cosmetic Regulation CE annex III")
        st.info("Source: EUR-Lex (Annex III - Restricted Substances)")
        if st.button("Scrape & Download", key="btn_annex3"):
            with st.spinner("Extracting Annex III..."):
                try:
                    csv_data = scrape_annex("III")
                    st.download_button(label="Download CSV", data=csv_data, file_name="annex_III.csv", mime="text/csv")
                    success, msg = sync_csv_to_db("cosmetic_annex3", csv_data, engine)
                    if success:
                        st.success("Extraction complete and Database synced!")
                    else:
                        st.error(f"Extraction complete, but Database sync failed: {msg}")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        st.subheader("Reach SVHC")
        st.info("Source: ECHA (Candidate list of substances of very high concern)")
        if st.button("Scrape & Download", key="btn_svhc"):
            with st.spinner("Extracting SVHC List..."):
                try:
                    csv_data = scrape_svhc()
                    st.download_button(label="Download CSV", data=csv_data, file_name="reach_svhc.csv", mime="text/csv")
                    success, msg = sync_csv_to_db("svhc", csv_data, engine)
                    if success:
                        st.success("Extraction complete and Database synced!")
                    else:
                        st.error(f"Extraction complete, but Database sync failed: {msg}")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.subheader("CA Prop65")
        st.info("Source: OEHHA (Proposition 65 List)")
        st.link_button("Go to OEHHA Page (to copy CSV link)", "https://oehha.ca.gov/proposition-65/proposition-65-list", use_container_width=True)
        prop65_manual_url = st.text_input(
            "Manual CSV Link (Optional)",
            placeholder="Paste the .csv link here...",
            help="If the auto-scraper fails (blocked by firewall), click the button above, right-click 'Proposition 65 List (CSV)', 'Copy link address', and paste it here."
        )
        if st.button("Scrape & Download", key="btn_prop65"):
            with st.spinner("Fetching latest Prop 65 CSV..."):
                try:
                    csv_data = scrape_prop65(manual_url=prop65_manual_url if prop65_manual_url else None)
                    st.download_button(label="Download CSV", data=csv_data, file_name="ca_prop65.csv", mime="text/csv")
                    success, msg = sync_csv_to_db("prop65", csv_data, engine)
                    if success:
                        st.success("Extraction complete and Database synced!")
                    else:
                        st.error(f"Extraction complete, but Database sync failed: {msg}")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()

    # --- Customer / Internal Lists Section ---
    st.header("Customer / Internal Lists")

    st.subheader("Export Existing Data")
    customer_lists = get_customer_lists(engine)
    list_options = {display: table for table, display in customer_lists}

    if list_options:
        col_export, col_import = st.columns(2)

        with col_export:
            export_display = st.selectbox("Select a list to export", list(list_options.keys()), key="dl_select")
            export_table = list_options[export_display]
            if st.button("Export as CSV", key="btn_dl_customer", use_container_width=True):
                with st.spinner("Preparing export..."):
                    try:
                        csv_data = download_customer_list(engine, export_table)
                        st.download_button(
                            label=f"Save {export_display} CSV",
                            data=csv_data,
                            file_name=f"{export_table}.csv",
                            mime="text/csv",
                            key="dl_customer_file"
                        )
                    except Exception as e:
                        st.error(f"Error: {e}")

        with col_import:
            upload_display = st.selectbox("Select a list to upload to", list(list_options.keys()), key="ul_select")
            upload_table = list_options[upload_display]
            uploaded_file = st.file_uploader(
                "Upload updated CSV or Excel",
                type=["csv", "xlsx", "xls"],
                key="ul_file"
            )
            if uploaded_file:
                if st.button("Upload & Sync to Database", key="btn_ul_customer", use_container_width=True):
                    st.session_state["confirm_upload"] = True

            if st.session_state.get("confirm_upload"):
                st.warning(f"Are you sure you want to replace ALL data in **{upload_display}**? This cannot be undone.")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Yes, update " + upload_display, key="btn_confirm_yes", use_container_width=True):
                        st.session_state["confirm_upload"] = False
                        with st.spinner("Converting CAS numbers and syncing..."):
                            success, msg = upload_customer_list(engine, upload_table, uploaded_file)
                            if success:
                                st.success(f"Synced to '{upload_display}'! CAS numbers converted to database format.")
                            else:
                                st.error(f"Upload failed: {msg}")
                with col_no:
                    if st.button("Cancel", key="btn_confirm_no", use_container_width=True):
                        st.session_state["confirm_upload"] = False
                        st.rerun()
    else:
        st.info("No customer lists found. Click 'Create & Sync Database Tables' above first.")

    # Create new customer list from template
    st.divider()
    st.subheader("Create New Customer List")
    template_csv = "chemical_name,cas_no,classification,limits\nExample Chemical,206-44-0,Prohibited,Max 0.1%\n"
    st.download_button(
        label="Download Blank Template",
        data=template_csv,
        file_name="customer_list_template.csv",
        mime="text/csv",
        key="dl_template",
        use_container_width=True
    )
    st.markdown("Fill in the template above, then upload it here to create a new list.")

    col_name, col_table = st.columns(2)
    with col_name:
        new_display = st.text_input("Display Name", placeholder="e.g. Estee Lauder", key="new_display")
    with col_table:
        new_table = st.text_input("Table Name (lowercase, no spaces)", placeholder="e.g. estee_lauder", key="new_table")

    new_file = st.file_uploader(
        "Upload filled template CSV or Excel",
        type=["csv", "xlsx", "xls"],
        key="new_list_file"
    )

    if new_file and new_display and new_table:
        if st.button("Create List & Import Data", key="btn_create_list", use_container_width=True):
            st.session_state["confirm_create"] = True

        if st.session_state.get("confirm_create"):
            st.warning(f"This will create a new table **{new_table}** and import the uploaded data. Continue?")
            col_cy, col_cn = st.columns(2)
            with col_cy:
                if st.button(f"Yes, create {new_display}", key="btn_create_yes", use_container_width=True):
                    st.session_state["confirm_create"] = False
                    with st.spinner("Creating table and importing data..."):
                        success, msg = add_customer_list(engine, new_table, new_display)
                        if not success:
                            st.error(f"Failed to create table: {msg}")
                        else:
                            success, msg = upload_customer_list(engine, new_table, new_file)
                            if success:
                                st.success(f"Created '{new_display}' and imported data! Refresh to see it in the dropdowns above.")
                            else:
                                st.error(f"Table created but import failed: {msg}")
            with col_cn:
                if st.button("Cancel", key="btn_create_no", use_container_width=True):
                    st.session_state["confirm_create"] = False
                    st.rerun()
