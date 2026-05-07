#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Sets each story as the GitHub parent of its task issues using the
    sub-issues REST API.  Skips any task that already has a parent (HTTP 422).
#>

$ErrorActionPreference = "SilentlyContinue"
$GH   = "C:\Program Files\GitHub CLI\gh.exe"
$REPO = "biteberry/project-intelligent"

# Map: story → tasks  (string keys to avoid OrderedDictionary positional index ambiguity)
$storyTasks = [ordered]@{
    "44" = @(57, 58, 59, 60, 61)
    "45" = @(62, 63, 64, 65)
    "46" = @(66, 67, 68)
    "47" = @(69, 70, 71)
    "48" = @(72, 73, 74)
    "49" = @(75, 76, 77)
    "50" = @(78, 79, 80)
    "52" = @(81, 82, 83)
    "53" = @(84, 85, 86)
    "54" = @(87, 88, 89)
    "55" = @(90, 91)
    "56" = @(92, 93, 94)
}

foreach ($story in $storyTasks.Keys) {
    Write-Host "`n=== Story #$story ===" -ForegroundColor Cyan
    foreach ($task in $storyTasks[$story]) {
        # Get the database (numeric) ID of the task issue
        $id = & $GH api /repos/$REPO/issues/$task --jq '.id' 2>&1
        if (-not $id -or $id -match "error|Error") {
            Write-Host "  #$task  SKIP (could not fetch id: $id)" -ForegroundColor Yellow
            continue
        }

        # Attempt to add task as sub-issue of story
        $result = & $GH api --method POST /repos/$REPO/issues/$story/sub_issues `
            --field sub_issue_id=$id 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Host "  #$task  linked as sub-issue of #$story" -ForegroundColor Green
        } elseif ($result -match "duplicate|one parent") {
            Write-Host "  #$task  already linked (skipped)" -ForegroundColor DarkGray
        } else {
            Write-Host "  #$task  ERROR: $result" -ForegroundColor Red
        }
    }
}

Write-Host "`n=== Done ===" -ForegroundColor Green
