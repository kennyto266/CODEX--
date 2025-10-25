import re
import os

specs = [
    "openspec/changes/add-alternative-data-framework/specs/correlation-analysis/spec.md",
    "openspec/changes/add-alternative-data-framework/specs/backtest-integration/spec.md",
]

for spec_file in specs:
    with open(spec_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix requirement descriptions that don't start with "The system SHALL"
    # Pattern: ### Requirement: XXXX\n\nDescription text without SHALL
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        new_lines.append(lines[i])
        
        # If this is a Requirement line
        if lines[i].startswith('### Requirement:') and 'Sharpe' in lines[i]:
            # Check next non-empty line for description
            if i + 2 < len(lines) and lines[i+1] == '':
                desc = lines[i+2]
                if desc and not desc.startswith('####') and not desc.startswith('##'):
                    if not ('SHALL' in desc or 'MUST' in desc):
                        # Add SHALL
                        lines[i+2] = 'The system SHALL ' + desc[0].lower() + desc[1:] if desc else desc
        i += 1
    
    content = '\n'.join(new_lines)
    
    # Fix capability bullets
    content = re.sub(
        r'(#### Capability\n)((?:- [A-Z][^S].*\n)*)',
        lambda m: m.group(1) + re.sub(r'^- ([A-Z])', r'- System SHALL \1', m.group(2), flags=re.MULTILINE),
        content,
        flags=re.MULTILINE
    )
    
    # Fix duplicate "System SHALL System SHALL"
    content = content.replace('System SHALL System SHALL', 'System SHALL')
    
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed {spec_file}")

print("All specs fixed!")
