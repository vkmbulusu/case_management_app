import pandas as pd
from sqlalchemy.orm import sessionmaker
from models import Case
from db import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def import_cases_csv(file_path):
    # Expected columns matching Case fields (adjust for CSV headers)
    required_columns = [
        'seller_id', 'seller_name', 'specialist_id', 'specialist_name', 'marketplace', 'case_source', 'case_status', 'workstream',
        'listing_start_date', 'listing_completion_date', 'issue_type', 'complexity', 'priority', 'api_supported', 'integration_type',
        'seller_type', 'feedback_received', 'csat_score'
    ]
    
    try:
        df = pd.read_csv(file_path)
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"CSV missing required columns: {required_columns}")
        
        # Validate enums/values (basic example, expand as needed)
        df['api_supported'] = df['api_supported'].astype(bool)
        df['feedback_received'] = df['feedback_received'].astype(bool)
        
        session = SessionLocal()
        for _, row in df.iterrows():
            # Upsert by assuming CSV has case_id or generate one; here assuming new inserts
            case = Case(**row.to_dict())
            session.merge(case)  # merge for upsert if case_id present
            session.flush()
        session.commit()
        session.close()
        return f"Imported {len(df)} cases successfully."
    except Exception as e:
        return f"Error importing CSV: {str(e)}"