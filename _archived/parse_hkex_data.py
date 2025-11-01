#!/usr/bin/env python3
"""
Parse HKEX Daily Market Statistics HTML and extract real data
"""

import json
import re
from bs4 import BeautifulSoup
from pathlib import Path

# Find the latest HTML file
data_dir = Path("my-crawler/data")
html_files = sorted(data_dir.glob("*.html"), reverse=True)

if not html_files:
    print("No HTML files found!")
    exit(1)

latest_html = html_files[0]
print(f"Processing: {latest_html}")

with open(latest_html, 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')

# Find all tables
tables = soup.find_all('table')
print(f"\nTotal tables found: {len(tables)}")

# Extract meaningful data from each table
extracted_data = {
    "market_statistics": [],
    "market_activity": []
}

for idx, table in enumerate(tables):
    # Get table text for debugging
    table_text = table.get_text(strip=True)[:100]
    try:
        print(f"\nTable {idx}: {table_text[:50]}...")
    except:
        print(f"\nTable {idx}: [Content with special characters]")

    # Extract headers and rows
    rows = table.find_all('tr')
    if not rows:
        continue

    # Try to extract headers from first row
    first_row = rows[0]
    headers = []
    for th in first_row.find_all(['th', 'td']):
        text = th.get_text(strip=True)
        if text and len(text) > 0:
            headers.append(text)

    if not headers:
        continue

    print(f"Headers: {headers}")

    # Extract data rows
    table_data = {
        "headers": headers,
        "rows": []
    }

    for row_idx, row in enumerate(rows[1:]):
        cells = row.find_all(['td', 'th'])
        row_data = []
        for cell in cells:
            text = cell.get_text(strip=True)
            row_data.append(text)

        if row_data and any(cell for cell in row_data):  # Only if row has content
            table_data["rows"].append(row_data)
            # Print first few rows of real data
            if len(table_data["rows"]) <= 3:
                print(f"  Row {row_idx}: {row_data[:5]}")  # Print first 5 cells

    # Only keep tables with actual data (not just headers)
    if table_data["rows"]:
        # Try to categorize table
        first_header = headers[0].lower() if headers else ""
        if any(keyword in first_header for keyword in ["股份", "成交", "指數", "市場", "活動"]):
            extracted_data["market_statistics"].append(table_data)
        else:
            extracted_data["market_activity"].append(table_data)

# Save parsed data
output_file = data_dir / "hkex_parsed_data.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(extracted_data, f, ensure_ascii=False, indent=2)

print(f"\n✅ Data saved to: {output_file}")
print(f"Total tables extracted: {len(extracted_data['market_statistics']) + len(extracted_data['market_activity'])}")
