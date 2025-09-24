import streamlit as st
from pages.cases_list import show_cases_list
from pages.case_detail import show_case_detail

def main():
    st.set_page_config(page_title="Case Management App", layout="wide")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Cases List", "Case Detail"])
    
    if page == "Cases List":
        show_cases_list()
    elif page == "Case Detail":
        show_case_detail()

if __name__ == "__main__":
    main()
