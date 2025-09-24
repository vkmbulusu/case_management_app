from sqlalchemy import func
from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, TIMESTAMP, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Enum as SAEnum

Base = declarative_base()

class Case(Base):
    __tablename__ = "cases"
    
    case_id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(Integer, nullable=False)
    seller_name = Column(String(255), nullable=False)
    specialist_id = Column(Integer, nullable=False)
    specialist_name = Column(String(255), nullable=False)
    marketplace = Column(SAEnum('EU5', 'EU', '3PX', 'MENA', 'AU', 'SG', 'NA', 'JP', 'ZA', name="marketplace_enum"), nullable=False)
    case_source = Column(SAEnum('ASTRO', 'WINSTON', name="case_source_enum"), nullable=False)
    case_status = Column(SAEnum('SUBMITTED', 'AWAITING INFORMATION', 'CANCELLED', 'ON-HOLD', 'WIP', 'COMPLETED', name="case_status_enum"), nullable=False)
    workstream = Column(SAEnum('PAID', 'STRATEGIC_PRODUCT_SMART_CONNECT_EU', 'DSR', 'STRATEGIC_PRODUCT_SMART_CONNECT_MENA', 'STRATEGIC_DEVELOPER_LUXURY_NA', 'MIGRATION_M@UMP', 'STRATEGIC_DSR', 'STRATEGIC_DEVELOPER_LUXURY_EU', 'F3', 'LUXURY STORE', 'STRATEGIC_PRODUCT_SMART_CONNECT_AU', 'B2B', 'STRATEGIC_PRODUCT_MFG', 'BRAND_AGENCY', 'DSR_3PD', 'STRATEGIC_PRODUCT_SMART_CONNECT_AES_AU', name="workstream_enum"), nullable=False)
    listing_start_date = Column(TIMESTAMP, nullable=True)
    listing_completion_date = Column(TIMESTAMP, nullable=True)
    issue_type = Column(String(255), nullable=False)
    complexity = Column(SAEnum('Easy', 'Medium', 'Hard', name="complexity_enum"), nullable=False)
    priority = Column(SAEnum('Low', 'Medium', 'High', name="priority_enum"), nullable=False)
    api_supported = Column(Boolean, nullable=False)
    integration_type = Column(String(255), nullable=False)
    seller_type = Column(SAEnum('NEW', 'EXISTING', name="seller_type_enum"), nullable=False)
    feedback_received = Column(Boolean, nullable=False)
    csat_score = Column(DECIMAL(3,1), nullable=True)

class Update(Base):
    __tablename__ = "updates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    note = Column(String(1000), nullable=False)
    updated_by = Column(String(255), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False, default=func.now())
    sub_status = Column(SAEnum('INT_START', 'INT_WIP', 'ON_HOLD', 'PMA_DRAF', 'MAC', 'PAA_DRAF', 'AAC', 'PMA', 'PAA', 'ASSIGNED', 'KO_SENT', 'PMA_FUP_1', 'PMA_FUP_2', 'PMA_FUP_3', 'PAC', 'CANCELLED', 'Case_Created', 'PMCA', 'Note', 'PMA_FUP_4', 'SUPPORT', 'HANDOVER', name="sub_status_enum"), nullable=False)
