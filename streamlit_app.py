import streamlit as st
from pages.add_case import show_add_case
from pages.cases_list import show_cases_list
from pages.case_detail import show_case_detail
from db import create_db  # Add this import

def main():
    st.set_page_config(page_title="Case Management App", layout="wide")
    
    # Create database tables if they don't exist (call once per app load)
    create_db()
    from db import SessionLocal
from models import Case, Update

# Add sample data
session = SessionLocal()
sample_case = Case(
    seller_id=12345, seller_name="Sample Seller", specialist_id=67890,
    specialist_name="John Doe", marketplace="NA", case_source="ASTRO",
    case_status="SUBMITTED", workstream="PAID", issue_type="Test Issue",
    complexity="Medium", priority="High", api_supported=True,
    integration_type="API v1", seller_type="NEW", feedback_received=False,
    csat_score=4.5
)
session.add(sample_case)
session.commit()
session.close()
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Cases List", "Case Detail","Add Case"])
    
    if page == "Cases List":
        show_cases_list()
    elif page == "Case Detail":
        show_case_detail()
    elif page == "Add Case":
        show_add_case()

if __name__ == "__main__":
    main()