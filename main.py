import streamlit as st
import os
from sqlalchemy import create_engine, text, inspect, Column, String, JSON, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Database Setup ---

# Primary Database (for results, etc.)
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    st.error("DATABASE_URL not found. Please set it in your .env file.")
    st.stop()

# Compliance/Regulatory Database
COMPLIANCE_DATABASE_URL = os.environ.get("ComplanceDATABASE_URL") or DATABASE_URL

# SQLAlchemy engines
engine = create_engine(DATABASE_URL)
compliance_engine = create_engine(COMPLIANCE_DATABASE_URL)

Base = declarative_base()

# Define the table structure for storing results
class Result(Base):
    __tablename__ = 'results'
    session_id = Column(String, primary_key=True)
    agent_type = Column(String, primary_key=True)
    data = Column(JSON)
    filename = Column(String)  # Added filename column
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def init_db():
    """Initializes the database and creates the results table if it doesn't exist."""
    try:
        with engine.connect() as connection:
            inspector = inspect(engine)
            if not inspector.has_table("results"):
                print("Creating 'results' table...")
                Base.metadata.create_all(engine)
                print("Table 'results' created.")
            else:
                print("Table 'results' already exists.")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        st.error(f"Database connection failed. Please check your Supabase setup. Error: {e}")
        st.stop()

# Initialize Database
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

# --- Streamlit App ---

import engAssistant
import complianceAssistant
import qualityRagChat
import regulatory_scraper

def regulatory_scraper_page(engine):
    st.title("🌐 Regulatory Scraper")
    st.markdown("""
    Generate and download the latest data from European and International regulatory sources. 
    All scrapers are optimized for speed and handle merged table cells automatically.
    """)
    # Database Management
    st.subheader("🛠️ Database Setup")
    st.write("Click below to create or update the required tables in Supabase (`cmr`, `annex2`, `annex3`, `svhc`, `prop65`, etc.).")
    if st.button("🚀 Create & Sync Database Tables", use_container_width=True):
        with st.spinner("Synchronizing schema..."):
            if regulatory_scraper.init_regulatory_db(engine):
                st.success("Successfully created/verified all tables: `cmr`, `annex2`, `annex3`, `svhc`, `prop65`, `extra`, `LOreal`.")
            else:
                st.error("Failed to synchronize database. Check logs.")
    
    st.link_button("🔗 Open Supabase Dashboard", "https://supabase.com/dashboard/project/ixsxmovayvtdeejdokvf", use_container_width=True)

    st.divider()

    # Scrapers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("CMR CLC Regulation")
        st.info("Source: Publications Office of the EU (DOC_2 - Table 3)")
        if st.button("🚀 Scrape & Download", key="btn_clp"):
            with st.spinner("Extracting classification data..."):
                try:
                    csv_data = regulatory_scraper.scrape_table_3_clp()
                    st.download_button(label="⬇️ Download CSV", data=csv_data, file_name="cmr_clc_regulation.csv", mime="text/csv")
                    
                    # Automatic Sync
                    success, msg = regulatory_scraper.sync_csv_to_db("cmr", csv_data, engine)
                    if success:
                        st.success("✅ Extraction complete and Database synced!")
                    else:
                        st.error(f"⚠️ Extraction complete, but Database sync failed: {msg}")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.subheader("Cosmetic Regulation CE annex II")
        st.info("Source: EUR-Lex (Annex II - Prohibited Substances)")
        if st.button("🚀 Scrape & Download", key="btn_annex2"):
            with st.spinner("Extracting Annex II..."):
                try:
                    csv_data = regulatory_scraper.scrape_annex("II")
                    st.download_button(label="⬇️ Download CSV", data=csv_data, file_name="annex_II.csv", mime="text/csv")
                    
                    # Automatic Sync
                    success, msg = regulatory_scraper.sync_csv_to_db("cosmetic_annex2", csv_data, engine)
                    if success:
                        st.success("✅ Extraction complete and Database synced!")
                    else:
                        st.error(f"⚠️ Extraction complete, but Database sync failed: {msg}")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.subheader("Cosmetic Regulation CE annex III")
        st.info("Source: EUR-Lex (Annex III - Restricted Substances)")
        if st.button("🚀 Scrape & Download", key="btn_annex3"):
            with st.spinner("Extracting Annex III..."):
                try:
                    csv_data = regulatory_scraper.scrape_annex("III")
                    st.download_button(label="⬇️ Download CSV", data=csv_data, file_name="annex_III.csv", mime="text/csv")
                    
                    # Automatic Sync
                    success, msg = regulatory_scraper.sync_csv_to_db("cosmetic_annex3", csv_data, engine)
                    if success:
                        st.success("✅ Extraction complete and Database synced!")
                    else:
                        st.error(f"⚠️ Extraction complete, but Database sync failed: {msg}")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        st.subheader("Reach SVHC")
        st.info("Source: ECHA (Candidate list of substances of very high concern)")
        if st.button("🚀 Scrape & Download", key="btn_svhc"):
            with st.spinner("Extracting SVHC List..."):
                try:
                    csv_data = regulatory_scraper.scrape_svhc()
                    st.download_button(label="⬇️ Download CSV", data=csv_data, file_name="reach_svhc.csv", mime="text/csv")
                    
                    # Automatic Sync
                    success, msg = regulatory_scraper.sync_csv_to_db("svhc", csv_data, engine)
                    if success:
                        st.success("✅ Extraction complete and Database synced!")
                    else:
                        st.error(f"⚠️ Extraction complete, but Database sync failed: {msg}")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.subheader("CA Prop65")
        st.info("Source: OEHHA (Proposition 65 List)")
        
        # Manual Link Fallback UI
        st.link_button("📂 Go to OEHHA Page (to copy CSV link)", "https://oehha.ca.gov/proposition-65/proposition-65-list", use_container_width=True)
        
        prop65_manual_url = st.text_input(
            "🔗 Manual CSV Link (Optional)", 
            placeholder="Paste the .csv link here...",
            help="If the auto-scraper fails (blocked by firewall), click the button above, right-click 'Proposition 65 List (CSV)', 'Copy link address', and paste it here."
        )
        
        if st.button("🚀 Scrape & Download", key="btn_prop65"):
            with st.spinner("Fetching latest Prop 65 CSV..."):
                try:
                    csv_data = regulatory_scraper.scrape_prop65(manual_url=prop65_manual_url if prop65_manual_url else None)
                    st.download_button(label="⬇️ Download CSV", data=csv_data, file_name="ca_prop65.csv", mime="text/csv")
                    
                    # Automatic Sync
                    success, msg = regulatory_scraper.sync_csv_to_db("prop65", csv_data, engine)
                    if success:
                        st.success("✅ Extraction complete and Database synced!")
                    else:
                        st.error(f"⚠️ Extraction complete, but Database sync failed: {msg}")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.subheader("others / L'Oreal")
        st.warning("Manual upload required for these specific private lists.")
        st.write("- **others**: Proprietary extra lists")
        st.write("- **L'Oreal**: L'Oreal specific prohibited lists")

st.set_page_config(
    page_title="Meiyume AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application function"""
    st.sidebar.markdown(
        f'''
        <div class="sidebar-logo">
            <img src="https://meiyume-website-media.s3.ap-southeast-1.amazonaws.com/wp-content/uploads/2020/08/14174032/Meiyume_footer_logo-e1667547906481.png" width="200">
        </div>
        ''',
        unsafe_allow_html=True
    )
    st.sidebar.title("🎯 Navigation")


    page = st.sidebar.selectbox(
        "Choose an Assistant",
        ["CAD Analysis", "Compliance Checker", "Quality RAG Chat", "Regulatory Scraper"],
    )

    # Pass the database engine to the assistants
    db_engine = engine

    if page == "CAD Analysis":
        engAssistant.engineering_assistant(db_engine)
    elif page == "Compliance Checker":
        complianceAssistant.compliance_assistant(compliance_engine)
    elif page == "Quality RAG Chat":
        qualityRagChat.quality_rag_chat()
    elif page == "Regulatory Scraper":
        regulatory_scraper_page(compliance_engine)

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Version:** 5.1.0")
    st.sidebar.markdown("**Powered by:** Meiyume AI")

if __name__ == "__main__":
    main()
