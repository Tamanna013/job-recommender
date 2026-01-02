import streamlit as st
import pandas as pd
import sqlite3
from serpapi import GoogleSearch

# --- CONFIGURATION ---
# Replace with your actual key from https://serpapi.com/dashboard
API_KEY = "" 
DB_NAME = "my_job_tracker.db"

# --- DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs 
                 (id TEXT PRIMARY KEY, title TEXT, company TEXT, 
                  location TEXT, source TEXT, link TEXT)''')
    conn.commit()
    conn.close()

# --- API HELPERS ---
def get_credits():
    """Checks your remaining SerpApi balance."""
    try:
        search = GoogleSearch({"api_key": API_KEY})
        return search.get_account().get("plan_searches_left", 0)
    except:
        return "N/A"

def fetch_top_10(role, location):
    """Fetches the top 10 results from Google Jobs."""
    params = {
        "engine": "google_jobs",
        "q": f"{role} {location}",
        "api_key": API_KEY,
        "hl": "en"
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    
    if "error" in results:
        st.error(f"Error: {results['error']}")
        return []
        
    return results.get("jobs_results", [])

def get_job_details(job_id):
    """Fetches specific apply links and descriptions for a job."""
    params = {
        "engine": "google_jobs_listing",
        "q": job_id,
        "api_key": API_KEY
    }
    search = GoogleSearch(params)
    return search.get_dict()

# --- STREAMLIT UI ---
st.set_page_config(page_title="Universal Job Scraper", page_icon="💼")
init_db()

st.title("💼 Universal Job Scraper")
st.write("Fetching the latest 10 roles across LinkedIn, Indeed, and more.")

with st.sidebar:
    st.header("API Status")
    st.metric("Free Credits Left", get_credits())

col1, col2 = st.columns(2)
with col1:
    role_input = st.text_input("Job Role", "Data Analyst")
with col2:
    loc_input = st.text_input("Location", "Remote")

if st.button("Search Top 10 Jobs"):
    with st.spinner("Searching the web..."):
        jobs = fetch_top_10(role_input, loc_input)
        
        if jobs:
            for job in jobs:
                job_id = job.get("job_id")
                with st.expander(f"📌 {job.get('title')} - {job.get('company_name')}"):
                    st.write(f"**Location:** {job.get('location')}")
                    st.write(f"**Posted via:** {job.get('via')}")
                    
                    if st.button("Reveal Apply Links & Description", key=job_id):
                        details = get_job_details(job_id)
                        
                        st.markdown("### Description")
                        st.write(details.get("description", "No description available."))
                        
                        st.markdown("### Apply Here")
                        apply_options = details.get("apply_options", [])
                        if apply_options:
                            for option in apply_options:
                                st.markdown(f"🔗 [{option.get('title')}]({option.get('link')})")
                        else:
                            st.info("No direct apply links found.")
                            
                    if st.button("Save to My Pipeline", key=f"save_{job_id}"):
                        conn = sqlite3.connect(DB_NAME)
                        try:
                            c = conn.cursor()
                            c.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?)", 
                                     (job_id, job.get('title'), job.get('company_name'), 
                                      job.get('location'), job.get('via'), "#"))
                            conn.commit()
                            st.toast("Saved to database!")
                        except sqlite3.IntegrityError:
                            st.toast("Already saved!")
                        finally:
                            conn.close()
        else:
            st.warning("No jobs found. Try a different role.")

st.divider()
st.header("📋 My Saved Pipeline")
conn = sqlite3.connect(DB_NAME)
saved_df = pd.read_sql("SELECT title, company, location, source FROM jobs", conn)
conn.close()

if not saved_df.empty:
    st.table(saved_df)
else:

    st.write("Search and save jobs to see them here.")
