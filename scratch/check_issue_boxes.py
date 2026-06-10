import subprocess
import json
import re

def check_boxes(issue_num):
    print(f"Updating Issue #{issue_num}...")
    # Get current body
    result = subprocess.run(["gh", "issue", "view", str(issue_num), "--json", "body"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to fetch issue {issue_num}")
        return
        
    data = json.loads(result.stdout)
    body = data.get("body", "")
    
    # Replace all [ ] with [x] in the body
    new_body = re.sub(r'\[ \]', '[x]', body)
    
    if new_body == body:
        print(f"No unchecked boxes found in {issue_num}.")
        return
        
    # Update issue
    with open("temp_body.md", "w", encoding="utf-8") as f:
        f.write(new_body)
        
    update_res = subprocess.run(["gh", "issue", "edit", str(issue_num), "--body-file", "temp_body.md"])
    if update_res.returncode == 0:
        print(f"Successfully updated checkboxes in Issue #{issue_num}")
    else:
        print(f"Failed to update {issue_num}")

# Update the individual features
check_boxes(12)
check_boxes(13)
check_boxes(14)

# We also completed Silver Layer (J11) earlier, so let's check it off if needed
check_boxes(11)
# Update the Epic
check_boxes(24)

print("Done updating checkboxes.")
