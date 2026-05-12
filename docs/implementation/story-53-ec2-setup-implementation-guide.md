# Story #53 — EC2 t3.micro Python Environment Setup
## Implementation Guide (Step-by-Step)

**Branch:** `feature/issue-53-ec2-setup`  
**Parent Feature:** [#2] Environment Provisioning  
**Region:** `ap-south-1` (Mumbai)

---

## Current State (as of 2026-05-13)

| # | Task | Status | Notes |
|---|---|---|---|
| #155 | Create IAM instance profile | ✅ Done | `project-intelligent-ec2-profile` exists with `project-intelligent-ec2-role` attached |
| #58 | Write IAM policy JSON for EC2 | ⬜ Verify | Policies must include SSM + S3 + DynamoDB + Secrets Manager |
| #84 | Launch EC2 t3.micro | ✅ Done | Instance `i-004ede57a842280fe` running (standard AL2023 AMI with SSM Agent pre-installed) |
| #156 | Verify SSM Agent installed & Fleet Manager registration | ✅ Done | Agent 3.3.4108.0, Status: Online |
| #85 | Install Python 3.12 + dependencies via SSM | ✅ Done | Python 3.12.13, pip 23.2.1, venv at /opt/project-intelligent/venv |
| #86 | Verify SSM-only access (no SSH) | ✅ Done | sshd active but no inbound SG rule; $SSH_CONNECTION empty; IAM role confirmed |

---

## Pre-flight Checklist (Run Before Starting)

```powershell
# 1. Confirm AWS CLI identity
aws sts get-caller-identity --output table

# 2. Confirm region
aws configure get region

# 3. Confirm IAM role exists
aws iam get-role --role-name project-intelligent-ec2-role --query "Role.Arn" --output text

# 4. Confirm instance profile exists and role is attached
aws iam get-instance-profile --instance-profile-name project-intelligent-ec2-profile `
  --query "InstanceProfile.Roles[*].RoleName" --output text
```

**Expected outputs:**
- `arn:aws:iam::307828758318:role/project-intelligent-ec2-role`
- `project-intelligent-ec2-role`

---

## STEP 1 — Verify IAM Policies on EC2 Role (#58)

The EC2 role must have these AWS managed policies attached:

| Policy | Purpose |
|---|---|
| `AmazonSSMManagedInstanceCore` | Required for SSM Agent to connect |
| `AmazonS3FullAccess` or scoped S3 policy | Read/write Bronze/Silver/Gold buckets |
| `AmazonDynamoDBFullAccess` or scoped DynamoDB policy | Predictions + audit tables |
| `SecretsManagerReadWrite` | Read API keys at runtime |

```powershell
# Check attached policies
aws iam list-attached-role-policies `
  --role-name project-intelligent-ec2-role `
  --query "AttachedPolicies[*].PolicyName" `
  --output table
```

If any policy is missing, attach it:

```powershell
# SSM — required for SSM Agent to connect
aws iam attach-role-policy `
  --role-name project-intelligent-ec2-role `
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore

# S3 — read/write Bronze/Silver/Gold/Landing buckets
aws iam attach-role-policy `
  --role-name project-intelligent-ec2-role `
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# DynamoDB — write predictions + audit records
aws iam attach-role-policy `
  --role-name project-intelligent-ec2-role `
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

# Secrets Manager — read API keys at runtime
aws iam attach-role-policy `
  --role-name project-intelligent-ec2-role `
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```

> **Note:** These are AWS managed (broad) policies to unblock EC2 setup. Issue #58 will replace them with scoped custom policies via Terraform.

Expected output after all 4 attached:
```
----------------------------------
|    ListAttachedRolePolicies    |
+--------------------------------+
|  AmazonSSMManagedInstanceCore  |
|  SecretsManagerReadWrite       |
|  AmazonDynamoDBFullAccess      |
|  AmazonS3FullAccess            |
+--------------------------------+
```

> ✅ **#58 done when:** All 4 policies are listed in the output.

---

## STEP 2 — Get Default VPC and Subnet (#84 prerequisite)

We use the **default VPC** (no custom VPC needed — see architecture decision).

```powershell
# Get default VPC ID
aws ec2 describe-vpcs `
  --filters "Name=isDefault,Values=true" `
  --query "Vpcs[0].VpcId" `
  --output text `
  --region ap-south-1

# Get a default subnet in ap-south-1a
aws ec2 describe-subnets `
  --filters "Name=defaultForAz,Values=true" "Name=availabilityZone,Values=ap-south-1a" `
  --query "Subnets[0].SubnetId" `
  --output text `
  --region ap-south-1
```

**Actual values (2026-05-13):**
- VPC: `vpc-02cf51d92d20cc1af`
- Subnet: `subnet-0740f93c66e98412c`

---

## STEP 3 — Create Security Group (#84 prerequisite)

```powershell
aws ec2 create-security-group `
  --group-name "project-intelligent-ec2-sg" `
  --description "EC2: no inbound, HTTPS outbound only for SSM" `
  --vpc-id vpc-02cf51d92d20cc1af `
  --region ap-south-1
```

**Actual values (2026-05-13):**
- SG ID: `sg-0f9f13caaddcc87a4`
- SG ARN: `arn:aws:ec2:ap-south-1:307828758318:security-group/sg-0f9f13caaddcc87a4`

```powershell
$sgId = "sg-0f9f13caaddcc87a4"

# Verify: no inbound rules (should be empty)
aws ec2 describe-security-groups `
  --group-ids $sgId `
  --query "SecurityGroups[0].IpPermissions" `
  --region ap-south-1

# Outbound is already open by default (0.0.0.0/0 all traffic)
# That's fine — EC2 needs outbound HTTPS 443 to reach SSM endpoints
```

> **Architecture note:** SSM needs NO inbound rules. No port 22. No port 443 inbound.  
> Outbound 443 (HTTPS) to AWS endpoints is sufficient.

---

## STEP 4 — Find Latest Amazon Linux 2023 AMI (#84)

```powershell
aws ec2 describe-images `
  --owners "amazon" `
  --filters "Name=name,Values=al2023-ami-*-x86_64" "Name=state,Values=available" `
  --query "Images | sort_by(@, &CreationDate)[-1].{Id:ImageId,Name:Name,Date:CreationDate}" `
  --output table `
  --region ap-south-1
```

**Actual value (2026-05-13):**
- AMI ID: `ami-02c2e090547226058`
- Name: `al2023-ami-2023.11.20260509.0-kernel-6.12-x86_64`
- Date: `2026-05-09`

> **Why Amazon Linux 2023 (standard, not minimal)?** SSM Agent is pre-installed and enabled by default. The minimal AMI does NOT include SSM Agent.

---

## STEP 5 — Launch EC2 Instance (#84)

```powershell
$amiId    = "<ami-id-from-step-4>"
$subnetId = "<subnet-id-from-step-2>"
$sgId     = "<sg-id-from-step-3>"

aws ec2 run-instances `
  --image-id ami-02c2e090547226058 `
  --instance-type t3.micro `
  --iam-instance-profile Name="project-intelligent-ec2-profile" `
  --subnet-id $subnetId `
  --security-group-ids $sgId `
  --no-associate-public-ip-address `
  --count 1 `
  --tag-specifications `
    'ResourceType=instance,Tags=[{Key=Name,Value=project-intelligent-ec2},{Key=Project,Value=ProjectIntelligent},{Key=ManagedBy,Value=AWSCLI},{Key=Phase,Value=Phase1}]' `
  --metadata-options "HttpEndpoint=enabled,HttpTokens=required" `
  --region ap-south-1
```

> **Important flags:**
> - `--no-associate-public-ip-address` → no public IP (SSM doesn't need one in default VPC with internet gateway)
> - `--no-key-name` (omit `--key-name`) → no SSH key pair
> - `HttpTokens=required` → enables IMDSv2 (security best practice)

After running, save the `InstanceId` from the output:
```powershell
$instanceId = "i-004ede57a842280fe"

# Save to file for later use
Set-Content -Path "infra/ec2/instance-id.env" -Value "INSTANCE_ID=i-004ede57a842280fe"
```

**Actual values (2026-05-13):**
- Instance ID: `i-004ede57a842280fe` (t3.micro, AMI: `ami-02c2e090547226058` standard AL2023)
- Subnet: `subnet-0740f93c66e98412c` (ap-south-1a)
- IAM Profile: `project-intelligent-ec2-profile` ✅ attached at launch
- Public IP: auto-assigned by default subnet ✅

> ⚠️ Launch history:
> - `i-0c77536832df0d114` — terminated (t2.micro, wrong Free Tier type for ap-south-1)
> - `i-0ee57a3063eb2892b` — terminated (--no-associate-public-ip-address blocked SSM outbound)
> - `i-05fa9b4dc3ce6fe1f` — terminated (used minimal AMI — SSM Agent not included)
> - `i-004ede57a842280fe` — **current** ✅ (standard AL2023 with SSM Agent pre-installed)

Wait for instance to reach `running` state:
```powershell
aws ec2 wait instance-running --instance-ids $instanceId --region ap-south-1
Write-Host "Instance is running."
```

> ✅ **#84 done when:** Instance is in `running` state with profile attached and no SSH key.

---

## STEP 6 — Verify SSM Agent and Fleet Manager Registration (#156)

SSM Agent can take 2–5 minutes to register after the instance starts.

```powershell
# Wait ~3 minutes, then check:
aws ssm describe-instance-information `
  --filters "Key=InstanceIds,Values=$instanceId" `
  --query "InstanceInformationList[*].{Id:InstanceId,Status:PingStatus,Agent:AgentVersion}" `
  --output table `
  --region ap-south-1
```

**Actual output (2026-05-13):**
```
-----------------------------------------------------------------
|                  DescribeInstanceInformation                  |
+------------+-----------------------+----------------+---------+
|    Agent   |          Id           |   Platform     | Status  |
+------------+-----------------------+----------------+---------+
|  3.3.4108.0|  i-004ede57a842280fe  |  Amazon Linux  |  Online |
+------------+-----------------------+----------------+---------+
```

> ✅ **#156 done.** SSM Agent `3.3.4108.0` online on `i-004ede57a842280fe`.

> ✅ **#156 done when:** Instance shows `Online` in `describe-instance-information`.

---

## STEP 7 — Install Python 3.12 and Dependencies via SSM (#85)

```powershell
# Open an SSM session (interactive shell on the EC2 instance)
aws ssm start-session `
  --target $instanceId `
  --region ap-south-1
```

Once inside the session, run these commands **on the EC2 instance**:

```bash
# 1. Update packages
sudo dnf update -y

# 2. Verify Python version (Amazon Linux 2023 ships with Python 3.9)
python3 --version

# 3. Install Python 3.12
sudo dnf install python3.12 -y

# 4. Verify
python3.12 --version

# 5. Install pip for Python 3.12
python3.12 -m ensurepip --upgrade

# 6. Create project directory
sudo mkdir -p /opt/project-intelligent
sudo chown ec2-user:ec2-user /opt/project-intelligent

# 7. Clone the repo or copy requirements.txt
# (You will set up GitHub access in a later issue)
# For now, manually create requirements.txt or copy via SSM

# 8. Install dependencies
cd /opt/project-intelligent
pip3.12 install -r requirements.txt --no-cache-dir

# 9. Verify key packages
python3.12 -c "import yfinance, pandas, boto3; print('All packages OK')"

# 10. Exit the session
exit
```

> ✅ **#85 done when:** `python3.12` is available and all packages from `requirements.txt` install without errors.

---

## STEP 8 — Final SSM-Only Access Verification (#86)

```powershell
# 1. Verify SSM session works
aws ssm start-session --target $instanceId --region ap-south-1
# Type: systemctl status amazon-ssm-agent
# Expected: active (running)
# Type: exit

# 2. Verify port 22 is NOT accessible
aws ec2 describe-security-groups `
  --group-ids $sgId `
  --query "SecurityGroups[0].IpPermissions" `
  --region ap-south-1
# Expected: empty array [] — no inbound rules at all

# 3. Verify SSM Fleet Manager health check
aws ssm describe-instance-information `
  --filters "Key=InstanceIds,Values=$instanceId" `
  --query "InstanceInformationList[0].PingStatus" `
  --output text `
  --region ap-south-1
# Expected: Online
```

> ✅ **#86 done when:** SSM session opens, no port 22, PingStatus=Online.

---

## STEP 9 — Commit and Close Issues

```powershell
# Stage all changes
git add infra/ec2/instance-id.env
git add infra/terraform/modules/ec2/
git add docs/implementation/

# Commit
git commit -m "feat(ec2): launch t2.micro with SSM-only access, install Python 3.12

- IAM instance profile: project-intelligent-ec2-profile
- Security group: no inbound, HTTPS outbound
- SSM Agent verified Online in Fleet Manager
- Python 3.12 installed with project dependencies

Closes #84, #85, #86, #155, #156"

git push origin feature/issue-53-ec2-setup
```

Then open a PR and close all linked issues.

---

## Troubleshooting

### SSM Agent not showing in Fleet Manager

1. **Check IAM policy:** `AmazonSSMManagedInstanceCore` must be attached to the role
   ```powershell
   aws iam list-attached-role-policies --role-name project-intelligent-ec2-role
   ```

2. **Check outbound access:** Default VPC has an internet gateway — ensure the subnet has a route to `igw-*`
   ```powershell
   aws ec2 describe-route-tables `
     --filters "Name=association.subnet-id,Values=$subnetId" `
     --query "RouteTables[0].Routes[*].{Dest:DestinationCidrBlock,GW:GatewayId}" `
     --output table --region ap-south-1
   ```
   Expected: a route `0.0.0.0/0 → igw-xxxxxxxxx`

3. **Wait longer:** SSM registration can take up to 5 minutes on first boot.

4. **Check SSM agent inside instance via EC2 console:**
   - AWS Console → EC2 → Instances → Select instance → Connect → EC2 Instance Connect
   - Run: `sudo systemctl status amazon-ssm-agent`
   - If stopped: `sudo systemctl start amazon-ssm-agent`

---

## Architecture Reference

- [06_platform_mlops_observability_security.md](../architecture/06_platform_mlops_observability_security.md)
- [09_pipeline_orchestration_architecture.md](../architecture/09_pipeline_orchestration_architecture.md)
- **No custom VPC** — default VPC is the correct choice (see VPC architecture decision)
- **No SSH key pair** — SSM Session Manager is the only access method (NFR-05)
- **IMDSv2 required** — `HttpTokens=required` enforces metadata service security
