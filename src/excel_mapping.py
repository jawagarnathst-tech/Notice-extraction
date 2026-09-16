import csv
import os

EXCEL_PATH = r"c:\Users\c1755\Notice-extraction\Notice_Mapping_Extracted_IT Team(Notice Mapping).csv"

def load_mappings():
    """
    Reads the Notice Mapping CSV file and returns:
    - notice_type_to_manager: dict mapping Notice Type -> Notice Manager
    - allowed_notice_types: list of all valid Notice Types
    """
    notice_type_to_manager = {}
    allowed_notice_types = []

    if os.path.exists(EXCEL_PATH):
        try:
            with open(EXCEL_PATH, mode="r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if len(row) < 2:
                        continue
                    classification = row[0].strip()
                    notice_type = row[1].strip()
                    notice_manager = row[2].strip() if len(row) > 2 else ""

                    if notice_type:
                        allowed_notice_types.append(notice_type)
                        if notice_manager:
                            notice_type_to_manager[notice_type] = notice_manager
        except Exception as e:
            print(f"Warning: Failed to load Excel mapping: {e}")

    return notice_type_to_manager, list(set(allowed_notice_types))