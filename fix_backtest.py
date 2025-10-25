import re

file = "openspec/changes/add-alternative-data-framework/specs/backtest-integration/spec.md"

with open(file, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix requirements without "The system SHALL" in the description
replacements = [
    ("### Requirement: Alternative Data Signal Strategies\n\nImplement", 
     "### Requirement: Alternative Data Signal Strategies\n\nThe system SHALL implement"),
    ("### Requirement: Performance Metrics with Alternative Data\n\nCalculate",
     "### Requirement: Performance Metrics with Alternative Data\n\nThe system SHALL calculate"),
    ("### Requirement: Alternative Data Signal Validation\n\nEnsure",
     "### Requirement: Alternative Data Signal Validation\n\nThe system SHALL ensure"),
    ("### Requirement: Dashboard Alternative Data Strategy Results\n\nDisplay",
     "### Requirement: Dashboard Alternative Data Strategy Results\n\nThe system SHALL display"),
]

for old, new in replacements:
    content = content.replace(old, new)

with open(file, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed backtest-integration.md")
