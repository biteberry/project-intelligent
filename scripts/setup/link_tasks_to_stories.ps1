#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Updates each story body to list its child task issues as a checklist,
    creating visible parent-child links on GitHub.
#>

$ErrorActionPreference = "Stop"
$GH = "C:\Program Files\GitHub CLI\gh.exe"
$REPO = "biteberry/project-intelligent"

# Map: story number → array of task issue numbers
$storyTasks = @{
    44 = @(57, 58, 59, 60, 61)
    45 = @(62, 63, 64, 65)
    46 = @(66, 67, 68)
    47 = @(69, 70, 71)
    48 = @(72, 73, 74)
    49 = @(75, 76, 77)
    50 = @(78, 79, 80)
    52 = @(81, 82, 83)
    53 = @(84, 85, 86)
    54 = @(87, 88, 89)
    55 = @(90, 91)
    56 = @(92, 93, 94)
}

foreach ($storyNum in ($storyTasks.Keys | Sort-Object)) {
    $tasks = $storyTasks[$storyNum]

    Write-Host "=== Linking tasks to story #$storyNum ===" -ForegroundColor Cyan

    # Fetch current story body (via JSON to preserve newlines)
    $jsonOut = & $GH issue view $storyNum --repo $REPO --json body 2>&1
    $currentBody = ($jsonOut | ConvertFrom-Json).body

    # Build the child tasks checklist block
    $taskLines = $tasks | ForEach-Object { "- [ ] #$_" }
    $taskBlock = $taskLines -join "`n"

    # Replace the placeholder line or append the child tasks section
    if ($currentBody -match "_To be linked once task issues are created\._") {
        $newBody = $currentBody -replace "_To be linked once task issues are created\._", $taskBlock
    } else {
        # Section already has content or doesn't have the placeholder — append/replace
        # Try to replace an existing child task block between ## Child Tasks and the next ##
        if ($currentBody -match "## Child Tasks") {
            # Replace everything after "## Child Tasks\n" until next "##" or end of string
            $newBody = $currentBody -replace "(?s)(## Child Tasks\s*\n).*?(\n##|\z)", "`$1$taskBlock`$2"
        } else {
            # Append a new section
            $newBody = $currentBody + "`n`n## Child Tasks`n`n$taskBlock"
        }
    }

    # Write updated body to a temp file and use --body-file to avoid shell quoting issues
    $tmpFile = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllText($tmpFile, $newBody, [System.Text.Encoding]::UTF8)
    & $GH issue edit $storyNum --repo $REPO --body-file $tmpFile 2>&1 | Out-Null
    Remove-Item $tmpFile -ErrorAction SilentlyContinue
    Write-Host "  Story #$storyNum now links to tasks: $($tasks -join ', ')"
}

Write-Host "`n=== All stories updated with child task links ===" -ForegroundColor Green
