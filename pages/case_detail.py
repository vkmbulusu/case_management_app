import streamlit as st
from sqlalchemy.orm import sessionmaker
from models import Case, Update
from db import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def show_case_detail():
    st.title("Case Detail")
    
    # Query param or input for case_id (stub)
    case_id = st.number_input("Enter Case ID", value=1, step=1)
    
    session = SessionLocal()
    case = session.query(Case).filter(Case.case_id == case_id).first()
    updates = session.query(Update).filter(Update.case_id == case_id).all()
    session.close()
    
    if case:
        st.write(f"**Case ID:** {case.case_id}")
        st.write(f"**Seller:** {case.seller_name}")
        st.write(f"**Status:** {case.case_status}")
        st.write(f"**Marketplace:** {case.marketplace}")
        # Add more fields as needed
        
        st.subheader("Updates")
        if updates:
            for update in updates:
                st.write(f"- {update.timestamp}: {update.note} (by {update.updated_by}, sub-status: {update.sub_status})")
        else:
            st.write("No updates yet.")
    else:
        st.write("Case not found.")