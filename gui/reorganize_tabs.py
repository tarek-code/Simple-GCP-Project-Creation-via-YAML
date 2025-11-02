#!/usr/bin/env python3
"""
Script to reorganize Streamlit GUI resources into proper tabs.
This script moves resource blocks from outside tabs into their correct tab locations.
"""

def read_file(filepath):
    with open(filepath, 'r') as f:
        return f.readlines()

def write_file(filepath, lines):
    with open(filepath, 'w') as f:
        f.writelines(lines)

def add_indentation(lines, spaces=4):
    """Add indentation to lines"""
    indent = ' ' * spaces
    result = []
    for line in lines:
        if line.strip():  # Only add indent to non-empty lines
            result.append(indent + line)
        else:
            result.append(line)
    return result

def extract_resource_block(lines, start_line, end_line):
    """Extract a resource block (0-indexed)"""
    return lines[start_line:end_line]

def main():
    filepath = '/media/mario/NewVolume/Simple-GCP-Project-Creation-via-YAML/gui/streamlit_app.py'
    lines = read_file(filepath)

    print(f"Total lines in file: {len(lines)}")

    # Define resource blocks to move (line numbers are 1-indexed from user, convert to 0-indexed)
    # Format: (start_line_1indexed, end_line_1indexed_exclusive, target_tab, resource_name)
    # Verified checkbox line numbers from grep:
    # 2666: Compute Instances -> ends at 3971
    # 3971: Storage Buckets -> ends at 4028
    # 4028: Pub/Sub -> ends at 4065
    # 4065: Cloud Run -> ends at 4150
    # 4150: Cloud SQL -> ends at 4192
    # 4192: Artifact Registry -> ends at 4234
    # 4234: Secret Manager -> ends at 4270
    # 4270: DNS Zones -> ends at 4309
    # 4309: BigQuery -> ends at 4345
    # 4345: Cloud Functions -> ends at 4389
    # 4389: GKE -> ends at 4414
    # 4414: Cloud Router -> ends at 4435
    # 4435: Cloud NAT -> ends at 4456
    # 4456: Static IPs -> ends at 4497
    # 4497: Compute Disks -> ends at 4541
    # 4541: Redis -> ends at 4583
    # 4583: VPC Connectors -> ends at 4625
    resources_to_move = [
        # Tab 2: Compute (comment line, then checkbox line, then to next comment/end)
        (2665, 3970, 'tab2', 'Compute Instances'),  # 2665: comment, 2666: checkbox, ends before 3970
        (4388, 4413, 'tab2', 'GKE Cluster'),        # 4388: comment, 4389: checkbox, ends before 4413
        (4496, 4540, 'tab2', 'Compute Disks'),      # 4496: comment, 4497: checkbox, ends before 4540

        # Tab 1: Network
        (4413, 4434, 'tab1', 'Cloud Router'),       # 4413: comment, 4414: checkbox, ends before 4434
        (4434, 4455, 'tab1', 'Cloud NAT'),          # 4434: comment, 4435: checkbox, ends before 4455
        (4455, 4496, 'tab1', 'Static IPs'),         # 4455: comment, 4456: checkbox, ends before 4496
        (4582, 4625, 'tab1', 'VPC Connectors'),     # 4582: comment, 4583: checkbox, ends at 4625

        # Tab 3: Storage & Data
        (3970, 4027, 'tab3', 'Storage Buckets'),    # 3970: comment, 3971: checkbox, ends before 4027
        (4149, 4191, 'tab3', 'Cloud SQL'),          # 4149: comment, 4150: checkbox, ends before 4191
        (4308, 4344, 'tab3', 'BigQuery'),           # 4308: comment, 4309: checkbox, ends before 4344
        (4540, 4582, 'tab3', 'Redis'),              # 4540: comment, 4541: checkbox, ends before 4582

        # Tab 4: Security
        (4233, 4269, 'tab4', 'Secret Manager'),     # 4233: comment, 4234: checkbox, ends before 4269

        # Tab 5: Services
        (4064, 4149, 'tab5', 'Cloud Run'),          # 4064: comment, 4065: checkbox, ends before 4149
        (4344, 4388, 'tab5', 'Cloud Functions'),    # 4344: comment, 4345: checkbox, ends before 4388
        (4027, 4064, 'tab5', 'Pub/Sub'),            # 4027: comment, 4028: checkbox, ends before 4064
        (4191, 4233, 'tab5', 'Artifact Registry'),  # 4191: comment, 4192: checkbox, ends before 4233

        # Tab 6: Other
        (4269, 4308, 'tab6', 'DNS Zones'),          # 4269: comment, 4270: checkbox, ends before 4308
    ]

    # Convert to 0-indexed and sort by start line (descending) to extract from bottom up
    resources_to_move = [(s-1, e-1, tab, name) for s, e, tab, name in resources_to_move]
    resources_to_move.sort(key=lambda x: x[0], reverse=True)

    # Extract all resource blocks
    extracted_resources = {}
    for start, end, tab, name in resources_to_move:
        resource_lines = lines[start:end]
        if tab not in extracted_resources:
            extracted_resources[tab] = []
        extracted_resources[tab].append((name, resource_lines))
        print(f"Extracted {name} ({end-start} lines) for {tab}")

    # Now we need to find where each tab's content should go
    # Let's find the line numbers for tab markers
    tab_locations = {}
    for i, line in enumerate(lines):
        if 'with tab1:' in line:
            tab_locations['tab1'] = i
        elif 'with tab2:' in line:
            tab_locations['tab2'] = i
        elif 'with tab3:' in line:
            tab_locations['tab3'] = i
        elif 'with tab4:' in line:
            tab_locations['tab4'] = i
        elif 'with tab5:' in line:
            tab_locations['tab5'] = i
        elif 'with tab6:' in line:
            tab_locations['tab6'] = i

    print("\nTab locations:")
    for tab, line_num in sorted(tab_locations.items()):
        print(f"  {tab}: line {line_num + 1}")

    # Find where to insert content for each tab (after the --- markdown line)
    tab_insert_locations = {}
    for tab, start_line in tab_locations.items():
        # Look for the markdown("---") line after the tab start
        for i in range(start_line, start_line + 10):
            if i < len(lines) and 'st.markdown("---")' in lines[i]:
                # Insert after this line
                tab_insert_locations[tab] = i + 1
                break

    print("\nTab insert locations:")
    for tab, line_num in sorted(tab_insert_locations.items()):
        print(f"  {tab}: insert after line {line_num + 1}")

    print("\nExtracted resources by tab:")
    for tab in ['tab1', 'tab2', 'tab3', 'tab4', 'tab5', 'tab6']:
        if tab in extracted_resources:
            print(f"\n{tab}:")
            for name, _ in extracted_resources[tab]:
                print(f"  - {name}")

    # Now perform the actual reorganization
    print("\n" + "="*60)
    print("PERFORMING REORGANIZATION")
    print("="*60)

    # Step 1: Remove all extracted resource blocks from their original locations
    # Sort by start line descending so we can remove from bottom to top
    new_lines = lines.copy()
    for start, end, tab, name in resources_to_move:
        print(f"Removing {name} from lines {start+1}-{end+1}")
        # Remove the block
        del new_lines[start:end]

    # Step 2: Find new tab insertion locations after removals
    new_tab_locations = {}
    for i, line in enumerate(new_lines):
        if 'with tab1:' in line:
            new_tab_locations['tab1'] = i
        elif 'with tab2:' in line:
            new_tab_locations['tab2'] = i
        elif 'with tab3:' in line:
            new_tab_locations['tab3'] = i
        elif 'with tab4:' in line:
            new_tab_locations['tab4'] = i
        elif 'with tab5:' in line:
            new_tab_locations['tab5'] = i
        elif 'with tab6:' in line:
            new_tab_locations['tab6'] = i

    # Find where to insert content for each tab (after the --- markdown line)
    new_tab_insert_locations = {}
    for tab, start_line in new_tab_locations.items():
        # Look for the markdown("---") line after the tab start
        for i in range(start_line, min(start_line + 15, len(new_lines))):
            if 'st.markdown("---")' in new_lines[i]:
                # Check if there's a comment placeholder on the next line, if so replace it
                insert_line = i + 1
                # Skip any blank lines
                while insert_line < len(new_lines) and new_lines[insert_line].strip() == '':
                    insert_line += 1
                # Check if there's a comment about resources going here
                if insert_line < len(new_lines) and new_lines[insert_line].strip().startswith('#') and 'will' in new_lines[insert_line].lower():
                    # Skip comment lines
                    while insert_line < len(new_lines) and (new_lines[insert_line].strip().startswith('#') or new_lines[insert_line].strip() == ''):
                        insert_line += 1
                new_tab_insert_locations[tab] = insert_line
                break

    print("\nNew tab insert locations after removals:")
    for tab, line_num in sorted(new_tab_insert_locations.items()):
        print(f"  {tab}: insert at line {line_num + 1}")

    # Step 3: Insert resources into their respective tabs
    # Process tabs in FORWARD order and recalculate positions after each insertion
    for tab in ['tab1', 'tab2', 'tab3', 'tab4', 'tab5', 'tab6']:
        if tab not in extracted_resources or tab not in new_tab_insert_locations:
            continue

        # Find current insert position for this tab
        tab_start = None
        for i, line in enumerate(new_lines):
            if f'with {tab}:' in line:
                tab_start = i
                break

        if tab_start is None:
            print(f"Warning: Could not find {tab} in modified file")
            continue

        # Find the insert position (after markdown("---"))
        insert_pos = None
        for i in range(tab_start, min(tab_start + 15, len(new_lines))):
            if 'st.markdown("---")' in new_lines[i]:
                insert_pos = i + 1
                # Skip blank lines and comment placeholders
                while insert_pos < len(new_lines) and (new_lines[insert_pos].strip() == '' or
                      (new_lines[insert_pos].strip().startswith('#') and 'will' in new_lines[insert_pos].lower())):
                    insert_pos += 1
                break

        if insert_pos is None:
            print(f"Warning: Could not find insertion point in {tab}")
            continue

        print(f"\nInserting into {tab} at position {insert_pos + 1}:")

        # Reverse the resources for this tab so they appear in the original order
        resources_for_tab = list(reversed(extracted_resources[tab]))

        for name, resource_lines in resources_for_tab:
            print(f"  - {name} ({len(resource_lines)} lines)")
            # Add indentation (4 spaces)
            indented_lines = add_indentation(resource_lines, 4)
            # Add a blank line before each resource
            indented_lines = ['\n'] + indented_lines
            # Insert at position
            new_lines[insert_pos:insert_pos] = indented_lines
            # Note: We don't update insert_pos because we're inserting at the same position repeatedly,
            # which pushes previous insertions down

    # Step 4: Remove placeholder comments in tab2
    for i in range(len(new_lines)):
        if 'with tab2:' in new_lines[i]:
            # Look for comment placeholders
            for j in range(i, min(i+10, len(new_lines))):
                if '# Compute Instances section will go here' in new_lines[j]:
                    new_lines[j] = ''
                elif '# (Currently at line' in new_lines[j]:
                    new_lines[j] = ''
            break

    # Step 5: Write the reorganized file
    backup_filepath = filepath + '.backup'
    print(f"\n\nCreating backup at: {backup_filepath}")
    write_file(backup_filepath, lines)

    print(f"Writing reorganized file to: {filepath}")
    write_file(filepath, new_lines)

    print(f"\nReorganization complete!")
    print(f"Original file backed up to: {backup_filepath}")
    print(f"\nFinal file has {len(new_lines)} lines (was {len(lines)} lines)")

if __name__ == '__main__':
    main()
