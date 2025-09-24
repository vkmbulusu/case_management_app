import streamlit as st
from sqlalchemy.orm import sessionmaker
from models import Case
from db import engine
import datetime  # For date fields

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def show_add_case():
    st.title("Add New Case")
    
    # Form for case details
    with st.form("add_case_form"):
        st.subheader("Case Information")
        
        # Basic fields
        seller_id = st.number_input("Seller ID", min_value=1, step=1)
        seller_name = st.text_input("Seller Name")
        specialist_id = st.number_input("Specialist ID", min_value=1, step=1)
        specialist_name = st.text_input("Specialist Name")
        
        # Enums as selects
        marketplace = st.selectbox("Marketplace", ['EU5', 'EU', '3PX', 'MENA', 'AU', 'SG', 'NA', 'JP', 'ZA'])
        case_source = st.selectbox("Case Source", ['ASTRO', 'WINSTON'])
        case_status = st.selectbox("Case Status", ['SUBMITTED', 'AWAITING INFORMATION', 'CANCELLED', 'ON-HOLD', 'WIP', 'COMPLETED'])
        workstream = st.selectbox("Workstream", ['PAID', 'STRATEGIC_PRODUCT_SMART_CONNECT_EU', 'DSR', 'STRATEGIC_PRODUCT_SMART_CONNECT_MENA', 'STRATEGIC_DEVELOPER_LUXURY_NA', 'MIGRATION_M@UMP', 'STRATEGIC_DSR', 'STRATEGIC_DEVELOPER_LUXURY_EU', 'F3', 'LUXURY STORE', 'STRATEGIC_PRODUCT_SMART_CONNECT_AU', 'B2B', 'STRATEGIC_PRODUCT_MFG', 'BRAND_AGENCY', 'DSR_3PD', 'STRATEGIC_PRODUCT_SMART_CONNECT_AES_AU'])
        issue_type = st.text_input("Issue Type")
        complexity = st.selectbox("Complexity", ['Easy', 'Medium', 'Hard'])
        priority = st.selectbox("Priority", ['Low', 'Medium', 'High'])
        api_supported = st.checkbox("API Supported")
        integration_type = st.text_input("Integration Type")
        seller_type = st.selectbox("Seller Type", ['NEW', 'EXISTING'])
        feedback_received = st.checkbox("Feedback Received")
        csat_score = st.number_input("CSAT Score", min_value=0.0, max_value=5.0, step=0.1, value=0.0)
        
        # Dates (optional)
        listing_start_date = st.date_input("Listing Start Date", value=None)
        listing_completion_date = st.date_input("Listing Completion Date", value=None)
        
        submitted = st.form_submit_button("Add Case")
        
        if submitted:
            # Validation (basic)
            if not seller_name or not specialist_name:
                st.error("Seller and Specialist names are required.")
                return
            
            # Convert dates to datetime if provided
            start_dt = datetime.datetime.combine(listing_start_date, datetime.time.min) if listing_start_date else None
            completion_dt = datetime.datetime.combine(listing_completion_date, datetime.time.min) if listing_completion_date else None
            
            # Create and save
            session = SessionLocal()
            new_case = Case(
                seller_id=seller_id, seller_name=seller_name, specialist_id=specialist_id,
                specialist_name=specialist_name, marketplace=marketplace, case_source=case_source,
                case_status=case_status, workstream=workstream, listing_start_date=start_dt,
                listing_completion_date=completion_dt, issue_type=issue_type, complexity=complexity,
                priority=priority, api_supported=api_supported, integration_type=integration_type,
                seller_type=seller_type, feedback_received=feedback_received, csat_score=csat_score
            )
            session.add(new_case)
            session.commit()
            case_id = new_case.case_id  # Autoincremented
            session.close()
            
            st.success(f"Case added successfully! ID: {case_id}")
            # Optional: Clear form or redirect