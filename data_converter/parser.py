import csv
import io
from datetime import datetime
from typing import Dict, List, Optional

CSV_COLUMNS = [
    "Customer Code","Ship To","PO No","Customer Part No","Customer Part Revision",
    "Part No","Part Revision","Release No","Quantity","Due Date","Ship From",
    "EDI Kanban No","EDI Dock Code","EDI Line Code","EDI Line 11","EDI Line 12",
    "EDI Line 13","EDI Line 14","EDI Line 15","EDI Line 16","EDI Line 17",
    "EDI Line 18","EDI Line 19","EDI Line 20","EDI R Code","EDI Intermediate Consignee",
    "EDI Load Sequence No","EDI Lot No","EDI Batch","EDI Order No","EDI Dealer No",
    "Release Type","Vehicle ID","Rotation","Usepoint","Auto Create PO","Supplier Code",
    "Drop Ship PO No","Production Start Date","Schedule Type"
]

def fmt_date_yyyymmdd_to_mdy(s: str) -> str:
    """Convert YYYYMMDD -> M/D/YYYY without leading zeros."""
    dt = datetime.strptime(s, "%Y%m%d")
    return f"{dt.month}/{dt.day}/{dt.year}"

def safe_get(field_list, idx) -> Optional[str]:
    try:
        val = field_list[idx]
        return val if val != "" else None
    except IndexError:
        return None

def parse_txt_to_rows(txt: str) -> List[Dict[str, Optional[str]]]:
    """
    Parse GHSP-style TXT into a list of dict rows matching CSV_COLUMNS.

    Strategy:
      - Maintain current '30' context for each following '50' schedule line.
      - On every '50', emit a row filled from the active '30' + that '50'.
    """
    rows: List[Dict[str, Optional[str]]] = []

    current_30 = {
        "po_no": None,            # 30 field[4]
        "cust_part": None,        # 30 field[3]
        "cust_part_rev": None,    # 30 field[2]
        "release_no": None,       # 30 field[7]
    }

    # Global constants (derived from your example CSV)
    CUSTOMER_CODE = "GHSP"
    SHIP_TO = "Shipping-Hart"
    SHIP_FROM_LITERAL = "Division: IG"

    for raw_line in txt.splitlines():
        if not raw_line.strip():
            continue
        parts = raw_line.split("|")
        rec = parts[0]

        # 30|120|A|<cust_part>|<PO>|1|EA|<release_no>|...
        if rec == "30":
            current_30["cust_part_rev"] = safe_get(parts, 2)
            current_30["cust_part"] = safe_get(parts, 3)
            current_30["po_no"] = safe_get(parts, 4)
            current_30["release_no"] = safe_get(parts, 7)

        # 50 schedule lines → one CSV row each, using active 30 context
        elif rec == "50" and current_30["cust_part"]:
            # Example forms seen:
            # 50||D|C|9504|20250904|||757692||9504
            # 50||W|D|9216|20250914|||781740||9216
            # positions: 0=50,1=?,2=horizon (D/W/M),3=?,4=qty,5=date,...
            horizon = safe_get(parts, 2) or ""
            qty = None
            date_raw = None

            # find first integer-like as qty and next 8-digit as date
            # (robust if extra empties shift positions)
            for i in range(2, len(parts)):
                p = parts[i]
                if p and p.isdigit():
                    # 8-digit likely date, 1-6 digits likely qty; we need both
                    if qty is None and len(p) <= 6:
                        qty = p
                        # try next fields for date
                        # find the next 8-digit field
                        for j in range(i+1, len(parts)):
                            pj = parts[j]
                            if pj and len(pj) == 8 and pj.isdigit():
                                date_raw = pj
                                break
                        if date_raw:
                            break

            if not (qty and date_raw):
                # If the simplistic scan failed, fall back to common positions
                qty = safe_get(parts, 4)
                date_raw = safe_get(parts, 5)

            if not (qty and date_raw):
                continue  # skip malformed 50

            # Release Type logic
            release_type = "Firm" if horizon == "D" else "Forecast"

            row = {col: None for col in CSV_COLUMNS}
            row.update({
                "Customer Code": CUSTOMER_CODE,
                "Ship To": SHIP_TO,
                "PO No": current_30["po_no"],
                "Customer Part No": current_30["cust_part"],
                "Customer Part Revision": current_30["cust_part_rev"],
                "Part No": f"{current_30['cust_part']}-F",  # mimic sample CSV
                "Part Revision": None,
                "Release No": current_30["release_no"],
                "Quantity": int(qty),
                "Due Date": fmt_date_yyyymmdd_to_mdy(date_raw),
                "Ship From": SHIP_FROM_LITERAL,
                "Release Type": release_type,
            })
            rows.append(row)

        else:
            # ignore 10,11,35,36,39,45,70 etc.
            pass

    return rows

def generate_csv_content(rows: List[Dict[str, Optional[str]]]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return buf.getvalue().encode("utf-8")
