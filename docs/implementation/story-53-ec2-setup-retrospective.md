# Story #53 — EC2 Setup: Full Retrospective
## What We Did, Challenges Faced, and How We Fixed Them

**Date:** 2026-05-13  
**Branch:** `feature/issue-53-ec2-setup`  
**Final Instance:** `i-004ede57a842280fe` (t3.micro, ap-south-1, Online in SSM Fleet Manager)

---

## Overview

Story #53 required provisioning an EC2 instance on AWS with:
- Python 3.12 environment
- SSM-only access (no SSH, no key pair)
- IAM role with SSM + S3 + DynamoDB + Secrets Manager permissions
- Instance registered in AWS Systems Manager Fleet Manager

This document is a full walkthrough of every step taken, every mistake made, and how each was resolved.

---

## PHASE 1 — IAM Setup

### What We Did
Verified that the IAM role `project-intelligent-ec2-role` already existed from prior work (issue #44).  
Checked all 4 required policies were attached:

| Policy | Purpose |
|---|---|
| `AmazonSSMManagedInstanceCore` | Allows SSM Agent to connect to Systems Manager |
| `AmazonS3FullAccess` | Read/write Bronze/Silver/Gold S3 buckets |
| `AmazonDynamoDBFullAccess` | Write predictions and audit records |
| `SecretsManagerReadWrite` | Read API keys at runtime |

**Command used:**
```powershell
aws iam list-attached-role-policies `
  --role-name project-intelligent-ec2-role `
  --query "AttachedPolicies[*].PolicyName" `
  --output table
```

**Result:** All 4 policies confirmed ✅

---

## PHASE 2 — Networking Setup

### What We Did
Used the **default VPC** in ap-south-1 (no custom VPC needed — cost-free, simpler).

```powershell
# Default VPC
aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" ...
# VPC: vpc-02cf51d92d20cc1af

# Default subnet in ap-south-1a
aws ec2 describe-subnets --filters "Name=defaultForAz,Values=true" "Name=availabilityZone,Values=ap-south-1a" ...
# Subnet: subnet-0740f93c66e98412c (MapPublicIpOnLaunch=True)
```

**Created a dedicated security group** with:
- **Zero inbound rules** (no SSH, no HTTP, nothing)
- **All outbound allowed** (0.0.0.0/0) — required for SSM Agent to reach AWS endpoints

```powershell
aws ec2 create-security-group `
  --group-name "project-intelligent-ec2-sg" `
  --description "EC2: no inbound, HTTPS outbound only for SSM" `
  --vpc-id vpc-02cf51d92d20cc1af `
  --region ap-south-1
# SG: sg-0f9f13caaddcc87a4
```

**Result:** VPC, subnet, and SG confirmed ✅

---

## PHASE 3 — AMI Selection

### What We Did
Searched for the latest Amazon Linux 2023 AMI.

**First attempt (WRONG):**
```powershell
--filters "Name=name,Values=al2023-ami-*-x86_64"
# Returned: ami-0627662924eb1b8c6 (al2023-ami-MINIMAL-...)
```

> ⚠️ **Challenge #1: Wrong AMI — minimal image has no SSM Agent**  
> We initially selected `al2023-ami-minimal-*` which does **not** include SSM Agent pre-installed. This caused all SSM registration attempts to fail silently.

**Fix — filter for standard (non-minimal) AMI:**
```powershell
--filters "Name=name,Values=al2023-ami-2023*-kernel-*-x86_64"
# Returned: ami-02c2e090547226058 (al2023-ami-2023.11.20260509.0-kernel-6.12-x86_64)
```

**Result:** Correct AMI identified ✅

---

## PHASE 4 — EC2 Launch Attempts

This phase had **3 failed attempts** before the final working launch.

---

### Attempt 1 — FAILED (Wrong instance type)

**Instance:** `i-0c77536832df0d114`  
**Problem:** Used `t2.micro` instead of `t3.micro`

> ⚠️ **Challenge #2: t2.micro is not Free Tier eligible in ap-south-1 (Mumbai)**  
> AWS Free Tier uses **t3.micro** in the Mumbai region, not t2.micro. t2.micro would have incurred charges.

**Fix:** Terminated and re-launched with `--instance-type t3.micro`

---

### Attempt 2 — FAILED (No public IP → SSM blocked)

**Instance:** `i-0ee57a3063eb2892b`  
**Problem:** Used `--no-associate-public-ip-address`

> ⚠️ **Challenge #3: SSM Agent needs outbound internet access**  
> We assumed SSM-only access meant the instance should have no public IP. This was wrong.  
> The default VPC has **no NAT gateway**. Without a public IP, the instance has no outbound internet route. SSM Agent couldn't reach `ssm.ap-south-1.amazonaws.com` to register.  
>
> **Key insight:** A public IP on the instance only enables **outbound** connectivity. The security group still has **zero inbound rules**, so the instance remains unreachable from the internet (no SSH possible). SSM works through the outbound HTTPS connection the agent initiates.

**Diagnostic checks run:**
```powershell
# Confirmed public IP was missing
aws ec2 describe-instances --instance-ids i-0ee57a3063eb2892b ...
# PublicIP: None

# Confirmed SG outbound was correct (0.0.0.0/0 all traffic)
aws ec2 describe-security-groups --group-ids sg-0f9f13caaddcc87a4 ...

# Confirmed subnet auto-assigns public IPs (MapPublicIpOnLaunch=True)
aws ec2 describe-subnets --subnet-ids subnet-0740f93c66e98412c ...
```

**Fix:** Terminated and re-launched **without** `--no-associate-public-ip-address`

---

### Attempt 3 — FAILED (Minimal AMI — no SSM Agent)

**Instance:** `i-05fa9b4dc3ce6fe1f`  
**Problem:** Used `ami-0627662924eb1b8c6` (minimal AMI)

> ⚠️ **Challenge #4: Amazon Linux 2023 minimal AMI does not include SSM Agent**  
> Network was now perfect (public IP ✅, outbound open ✅, subnet OK ✅) but SSM still returned empty results.  
> Root cause: The **minimal** AL2023 AMI strips out SSM Agent to reduce image size. Only the **standard** AL2023 AMI has it pre-installed and enabled.

**Fix:** Correct AMI filter — `al2023-ami-2023*` (not `al2023-ami-minimal*`):
```powershell
--filters "Name=name,Values=al2023-ami-2023*-kernel-*-x86_64"
# New AMI: ami-02c2e090547226058
```

---

### Attempt 4 — SUCCESS ✅

**Instance:** `i-004ede57a842280fe`

**Final launch command:**
```powershell
aws ec2 run-instances `
  --image-id ami-02c2e090547226058 `
  --instance-type t3.micro `
  --iam-instance-profile Name="project-intelligent-ec2-profile" `
  --subnet-id subnet-0740f93c66e98412c `
  --security-group-ids sg-0f9f13caaddcc87a4 `
  --count 1 `
  --metadata-options "HttpEndpoint=enabled,HttpTokens=required" `
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=project-intelligent-ec2},...]" `
  --region ap-south-1
```

**Key decisions in final command:**
| Flag | Reason |
|---|---|
| No `--key-name` | No SSH key — SSM only |
| No `--no-associate-public-ip-address` | Instance needs public IP for SSM outbound |
| `HttpTokens=required` | IMDSv2 enforced (security best practice) |
| `HttpEndpoint=enabled` | IMDSv2 metadata endpoint active |

---

## PHASE 5 — SSM Agent Verification (#156)

### What We Did
After instance reached `running` state, waited ~3 minutes for SSM Agent to register:

```powershell
aws ssm describe-instance-information `
  --filters "Key=InstanceIds,Values=i-004ede57a842280fe" `
  --query "InstanceInformationList[*].{Id:InstanceId,Status:PingStatus,Agent:AgentVersion,Platform:PlatformName}" `
  --output table `
  --region ap-south-1
```

**Result:**
```
-----------------------------------------------------------------
|                  DescribeInstanceInformation                  |
+------------+-----------------------+----------------+---------+
|    Agent   |          Id           |   Platform     | Status  |
+------------+-----------------------+----------------+---------+
|  3.3.4108.0|  i-004ede57a842280fe  |  Amazon Linux  |  Online |
+------------+-----------------------+----------------+---------+
```

✅ SSM Agent 3.3.4108.0 — Online

---

## PHASE 6 — Session Manager Plugin Installation

### What We Did
Tried to open an SSM interactive session:
```powershell
aws ssm start-session --target i-004ede57a842280fe --region ap-south-1
```

> ⚠️ **Challenge #5: Session Manager Plugin not installed on local machine**  
> `aws ssm start-session` requires a local plugin (`session-manager-plugin.exe`) that is separate from the AWS CLI itself.

**Fix:**
```powershell
# Download and install plugin
$url = "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/windows/SessionManagerPluginSetup.exe"
Invoke-WebRequest -Uri $url -OutFile "$env:TEMP\SessionManagerPluginSetup.exe"
Start-Process -FilePath "$env:TEMP\SessionManagerPluginSetup.exe" -ArgumentList "/S" -Wait -Verb RunAs
```

Plugin installed to: `C:\Program Files\Amazon\SessionManagerPlugin\bin\session-manager-plugin.exe`

> Note: After installation, a **new PowerShell window** must be opened for `aws ssm start-session` to find the plugin.

**Result:** Session opened successfully ✅

---

## PHASE 7 — Python 3.12 Environment Setup (#85)

### What We Did
Inside the SSM session on the EC2 instance:

**Step 1: Check Python version**
```bash
python3.12 --version
# Python 3.12.13 — already pre-installed on standard AL2023 ✅
```

**Step 2: Verify pip**
```bash
python3.12 -m pip --version
# pip 23.2.1 from /usr/lib/python3.12/site-packages/pip (python 3.12)
```

> No `dnf install` needed — Python 3.12 and pip are bundled with standard AL2023.

**Step 3: Create project directory and virtual environment**
```bash
sudo mkdir -p /opt/project-intelligent
sudo chown ssm-user:ssm-user /opt/project-intelligent
python3.12 -m venv /opt/project-intelligent/venv
source /opt/project-intelligent/venv/bin/activate
```

**Step 4: Install core dependencies**
```bash
pip install --upgrade pip
pip install boto3 pandas numpy requests
```

**Installed versions:**
| Package | Version |
|---|---|
| boto3 | 1.43.6 |
| botocore | 1.43.6 |
| pandas | 3.0.3 |
| numpy | 2.4.4 |
| requests | 2.34.0 |
| s3transfer | 0.17.0 |
| urllib3 | 2.7.0 |

**Step 5: Capture requirements**
```bash
pip freeze > /opt/project-intelligent/requirements.txt
```

`requirements.txt` also created in the repo root ✅

---

## PHASE 8 — SSM-Only Access Verification (#86)

### What We Did
Inside the SSM session, ran 3 verification checks:

```bash
# 1. Is sshd running?
sudo systemctl is-active sshd
# active

# 2. Is this an SSH connection?
echo $SSH_CONNECTION
# (empty — confirmed SSM session, not SSH)

# 3. Does the IAM role work?
aws sts get-caller-identity --region ap-south-1
# "Arn": "arn:aws:sts::307828758318:assumed-role/project-intelligent-ec2-role/i-004ede57a842280fe"
```

**Analysis:**
| Check | Result | Meaning |
|---|---|---|
| `sshd` is `active` | Normal on AL2023 | sshd runs but SG has zero inbound rules — port 22 is unreachable from internet |
| `$SSH_CONNECTION` empty | ✅ | Confirms we connected via SSM, not SSH |
| IAM role assumed | ✅ | Instance can access S3, DynamoDB, Secrets Manager, SSM |

---

## PHASE 9 — Commit and PR

### What We Did
Staged and committed all files on branch `feature/issue-53-ec2-setup`:

**Files committed:**
| File | Purpose |
|---|---|
| `docs/implementation/story-53-ec2-setup-implementation-guide.md` | Step-by-step implementation guide with all real values |
| `docs/implementation/story-53-ec2-setup-retrospective.md` | This document |
| `docs/implementation/issue-44-iam-instance-profile-guide.md` | IAM profile creation guide |
| `docs/implementation/issue-84-ec2-launch-ssm-guide.md` | EC2 launch guide |
| `docs/implementation/issue-84-ec2-ssm-troubleshooting.md` | SSM troubleshooting guide |
| `docs/architecture/ec2_ssm_architecture.md` | Architecture reference |
| `docs/prd/ec2_ssm_prd.md` | Product requirements |
| `requirements.txt` | Python dependencies captured from EC2 venv |
| `infra/iam/test-lock.txt` | IAM infra placeholder |
| `infra/s3/test-lock.txt` | S3 infra placeholder |

**Commit message:**
```
feat(ec2): EC2 t3.micro setup with SSM-only access (#53)

Closes #53, #84, #85, #86, #155, #156
```

---

## Summary of All Challenges and Fixes

| # | Challenge | Root Cause | Fix |
|---|---|---|---|
| 1 | Wrong AMI selected (minimal) | Filter `al2023-ami-*` matched minimal AMI | Changed filter to `al2023-ami-2023*` to get standard AMI |
| 2 | t2.micro used instead of t3.micro | Incorrect assumption about Free Tier | Re-launched with `--instance-type t3.micro` |
| 3 | SSM Agent not registering (no public IP) | Used `--no-associate-public-ip-address` in default VPC with no NAT gateway | Removed flag — default subnet auto-assigns public IP; SG has zero inbound so it's still secure |
| 4 | SSM Agent not registering (minimal AMI) | al2023-ami-minimal does not include SSM Agent | Re-launched with standard AL2023 AMI (`ami-02c2e090547226058`) |
| 5 | `aws ssm start-session` error | Session Manager Plugin not installed locally | Downloaded and installed `SessionManagerPluginSetup.exe` from AWS |

---

## Final State

| Resource | Value |
|---|---|
| EC2 Instance ID | `i-004ede57a842280fe` |
| Instance Type | `t3.micro` (Free Tier eligible in ap-south-1) |
| AMI | `ami-02c2e090547226058` (AL2023 standard, kernel 6.12) |
| Region / AZ | `ap-south-1` / `ap-south-1a` |
| VPC | `vpc-02cf51d92d20cc1af` (default) |
| Subnet | `subnet-0740f93c66e98412c` |
| Security Group | `sg-0f9f13caaddcc87a4` (0 inbound, all outbound) |
| IAM Profile | `project-intelligent-ec2-profile` |
| IAM Role | `project-intelligent-ec2-role` |
| SSM Agent | `3.3.4108.0` — Online |
| Python | `3.12.13` |
| Venv | `/opt/project-intelligent/venv` |
| Access Method | SSM Session Manager only (no SSH, no key pair) |
| IMDSv2 | Enforced (`HttpTokens=required`) |
