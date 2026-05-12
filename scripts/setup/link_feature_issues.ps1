# Load token from environment variable - NEVER hardcode tokens in source files
# Set it before running: $env:GITHUB_TOKEN = "your_token_here"
$token = $env:GITHUB_TOKEN
if (-not $token) { throw "GITHUB_TOKEN environment variable is not set. Run: `$env:GITHUB_TOKEN = 'your_pat'" }

$headers = @{
    Authorization = "Bearer $token"
    "X-GitHub-Api-Version" = "2022-11-28"
    "GraphQL-Features" = "sub_issues"
}

# Step 1: Get node IDs via GraphQL
$gql = @"
{
  "query": "{ repository(owner: \"biteberry\", name: \"project-intelligent\") { i2: issue(number: 2) { databaseId title } i45: issue(number: 45) { databaseId title } i142: issue(number: 142) { databaseId title } i143: issue(number: 143) { databaseId title } i144: issue(number: 144) { databaseId title } i140: issue(number: 140) { databaseId title } i141: issue(number: 141) { databaseId title } } }"
}
"@

$resp = Invoke-RestMethod -Uri "https://api.github.com/graphql" -Method Post -Headers $headers -Body $gql -ContentType "application/json"
$repo = $resp.data.repository

Write-Host "=== Database IDs ==="
Write-Host "Feature #2  (Env Provisioning):  $($repo.i2.databaseId)"
Write-Host "Story   #45 (S3 Buckets):        $($repo.i45.databaseId)"
Write-Host "Story   #142 (G0 Gate):          $($repo.i142.databaseId)"
Write-Host "Task    #140 (Object Lock):      $($repo.i140.databaseId)"
Write-Host "Task    #141 (Lifecycle fix):    $($repo.i141.databaseId)"
Write-Host "Task    #143 (G0 logic):         $($repo.i143.databaseId)"
Write-Host "Task    #144 (G0 unit tests):    $($repo.i144.databaseId)"

# Helper: add sub-issue using REST API
function Add-SubIssue($parentNum, $childDbId) {
    $url = "https://api.github.com/repos/biteberry/project-intelligent/issues/$parentNum/sub_issues"
    $body = @{ sub_issue_id = $childDbId } | ConvertTo-Json
    try {
        $r = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body -ContentType "application/json"
        Write-Host "  -> Linked child $childNodeId to parent #$parentNum (OK)"
    } catch {
        $msg = $_.Exception.Response.StatusCode
        Write-Host "  -> Link child $childNodeId to parent #$parentNum FAILED: $msg"
        Write-Host "     $_"
    }
}

Write-Host ""
Write-Host "=== Linking sub-issues ==="

# Link Story #45 -> Feature #2
Write-Host "Linking Story #45 -> Feature #2..."
Add-SubIssue 2 $repo.i45.databaseId

# Link Story #142 -> Feature #2 (Landing layer infra is Environment Provisioning)
Write-Host "Linking Story #142 -> Feature #2..."
Add-SubIssue 2 $repo.i142.databaseId

# Link Task #140 -> Story #45
Write-Host "Linking Task #140 -> Story #45..."
Add-SubIssue 45 $repo.i140.databaseId

# Link Task #141 -> Story #45
Write-Host "Linking Task #141 -> Story #45..."
Add-SubIssue 45 $repo.i141.databaseId

# Link Task #143 -> Story #142
Write-Host "Linking Task #143 -> Story #142..."
Add-SubIssue 142 $repo.i143.databaseId

# Link Task #144 -> Story #142
Write-Host "Linking Task #144 -> Story #142..."
Add-SubIssue 142 $repo.i144.databaseId

Write-Host ""
Write-Host "=== Done ==="
