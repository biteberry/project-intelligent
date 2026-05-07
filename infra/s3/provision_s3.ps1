$ErrorActionPreference = "Stop"

$accountId = "307828758318"
$region = "ap-south-1"

$buckets = @{
    "landing" = "project-intelligent-landing-$accountId"
    "bronze" = "project-intelligent-bronze-$accountId"
    "silver" = "project-intelligent-silver-$accountId"
    "gold" = "project-intelligent-gold-$accountId"
    "artifacts" = "project-intelligent-artifacts-$accountId"
}

# --- Step 1: Create Buckets ---
Write-Host "Creating 5 S3 Buckets in $region..."
foreach ($name in $buckets.Values) {
    Write-Host "  Creating s3://$name"
    aws s3 mb s3://$name --region $region | Out-Null
}

Write-Host "Saving bucket names to bucket-names.env..."
@"
LANDING_BUCKET=$($buckets['landing'])
BRONZE_BUCKET=$($buckets['bronze'])
SILVER_BUCKET=$($buckets['silver'])
GOLD_BUCKET=$($buckets['gold'])
ARTIFACTS_BUCKET=$($buckets['artifacts'])
"@ | Out-File -FilePath "bucket-names.env" -Encoding ASCII

# --- Step 2: Secure Buckets ---
Write-Host "Applying Security Baselines (Block Public Access & Encryption)..."
foreach ($name in $buckets.Values) {
    Write-Host "  Securing $name"
    
    # Block Public Access
    aws s3api put-public-access-block --bucket $name --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" | Out-Null
    
    # Server-Side Encryption (SSE-S3 AES256)
    # Using file:// to avoid Windows PowerShell JSON string escaping issues
    aws s3api put-bucket-encryption --bucket $name --server-side-encryption-configuration file://encryption-config.json | Out-Null
}

# --- Step 3: Enable Versioning ---
Write-Host "Enabling Versioning on Bronze, Silver, Gold, and Artifacts buckets..."
$versionedBuckets = @($buckets['bronze'], $buckets['silver'], $buckets['gold'], $buckets['artifacts'])
foreach ($name in $versionedBuckets) {
    Write-Host "  Versioning enabled for $name"
    aws s3api put-bucket-versioning --bucket $name --versioning-configuration Status=Enabled | Out-Null
}

# --- Step 4: Configure Lifecycle Policy ---
Write-Host "Applying 30-Day Expiration Lifecycle Policy to Landing bucket..."
aws s3api put-bucket-lifecycle-configuration --bucket $buckets['landing'] --lifecycle-configuration file://landing-lifecycle.json | Out-Null

Write-Host "All S3 provisioning steps completed successfully!"
