# create_github_feature_issues.ps1
# Creates all 21 FEATURE (epic) issues for PROJECT INTELLIGENT.
# Uses temp body files to avoid PowerShell markdown parsing issues.
# Usage: .\scripts\setup\create_github_feature_issues.ps1

$repo = "biteberry/project-intelligent"
$gh   = "C:\Program Files\GitHub CLI\gh.exe"
$tmp  = "$env:TEMP\gh_issue_body.md"
$M0=1; $M1=2; $M2=3; $M3=4; $M4=5; $M5=6; $M6=7; $M7=8

function New-Issue($title, $labels, $milestone, $body) {
    $body | Set-Content -Path $tmp -Encoding UTF8
    & $gh issue create --repo $repo --title $title --label $labels --milestone $milestone --body-file $tmp
}

Write-Host "Creating 21 Feature issues on $repo ..." -ForegroundColor Cyan

# FEATURE-001
New-Issue "[FEATURE-001] Architecture Phase Closure" `
  "type:feature,phase:0-setup,comp:docs,priority:critical" $M0 `
  "## Description`nClose architecture phase. Sign off PRD, create Phase 0 gate record.`n`n## PRD Reference`nAll FRs (design prerequisite)`n`n## Architecture Reference`ndocs/architecture/ docs/prd/PRD_v1.0.md docs/adr/`n`n## Child Stories`n- [ ] Phase 0 gate audit document`n- [ ] PRD v1.0 sign-off and approval`n- [ ] configs/position_sizing.yaml creation`n- [ ] All architecture docs pushed to GitHub (DONE)`n`n## Acceptance Criteria`n- [ ] All child stories closed`n- [ ] Phase 0 gate audit record exists with date and approval`n- [ ] configs/position_sizing.yaml committed to repo`n`n## Notes`nPer doc 07 Guardrail G4: no phase begins before previous phase exit criteria are signed off."
