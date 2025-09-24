import streamlit as st
from sqlalchemy.orm import sessionmaker
from models import Case
from db import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def show_cases_list():
    st.title("Cases List")
    
    # Filters (stubs)
    marketplace_filter = st.selectbox("Filter by Marketplace", ["All"] + ['EU5', 'EU', '3PX', 'MENA', 'AU', 'SG', 'NA', 'JP', 'ZA'])
    status_filter = st.selectbox("Filter by Status", ["All"] + ['SUBMITTED', 'AWAITING INFORMATION', 'CANCELLED', 'ON-HOLD', 'WIP', 'COMPLETED'])
    
    # Placeholder for fetching and displaying cases
    session = SessionLocal()
    cases = session.query(Case).limit(10).all()  # Stub: fetch with filters later
    session.close()
    
    if cases:
        st.table([{c.case_id: c.case_id, "Seller": c.seller_name, "Status": c.case_status, "Marketplace": c.marketplace} for c in cases])
    else:
        st.write("No cases found.")
    
    # Links to details (stub)
    st.write("Select a case to view details.")