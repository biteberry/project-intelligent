# Issue #84 — EC2 t2.micro Launch & SSM Setup Guide

**Repo:** biteberry/project-intelligent  
**Related Issues:** #53 (parent), #84 (this task)

---

## Overview
This guide provides step-by-step instructions to launch an EC2 t3.micro instance with Amazon Linux 2023, attach the correct IAM role, and enable SSM Session Manager access (no SSH). All steps are AWS CLI and PowerShell safe.

---

## Prerequisites
- IAM instance profile/role created (see issue #44, e.g., project-intelligent-ec2-role)
- AWS CLI configured for your account/region

---

## Step 1 — Find the Latest Amazon Linux 2023 AMI

```powershell
aws ec2 describe-images `
  --owners "amazon" `
  --filters "Name=name,Values=al2023-ami-*-x86_64" "Name=state,Values=available" `
  --query "Images | sort_by(@, &CreationDate)[-1].ImageId" `
  --output text `
  --region ap-south-1
```
- Save the output as `$amiId`.

---

## Step 2 — Launch the EC2 Instance

```powershell
$amiId = "ami-xxxxxxxxxxxxxxxxx"  # Use the value from Step 1
$instanceType = "t3.micro"  # Free Tier eligible in ap-south-1
$iamInstanceProfile = "project-intelligent-ec2-role"  # Replace with your IAM role name
$region = "ap-south-1"

aws ec2 run-instances `
  --image-id $amiId `
  --instance-type $instanceType `
  --iam-instance-profile Name=$iamInstanceProfile `
  --no-associate-public-ip-address `
  --count 1 `
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=project-intelligent-ec2}]' `
  --security-group-ids <your-sg-id> `
  --subnet-id <your-subnet-id> `
  --region $region
```
- Replace `<your-sg-id>` and `<your-subnet-id>` with your VPC values.
- No SSH key pair is associated (default for SSM-only access).

---

## Step 3 — Verify SSM Agent and Connectivity

1. Wait for the instance to be in `running` state:
   ```powershell
   aws ec2 describe-instances --filters Name=tag:Name,Values=project-intelligent-ec2 --query "Reservations[*].Instances[*].InstanceId" --output text --region $region
   ```
2. Check SSM registration:
   ```powershell
   aws ssm describe-instance-information --query "InstanceInformationList[*].InstanceId" --output text --region $region
   ```
   - Your instance ID should appear in the output.

---

## Step 4 — Save the Instance ID

```powershell
$instanceId = "i-xxxxxxxxxxxxxxxxx"  # Use the value from Step 3
Set-Content -Path "infra/ec2/instance-id.env" -Value "INSTANCE_ID=$instanceId"
```

---

## Step 5 — (Optional) Connect via SSM Session Manager

```powershell
aws ssm start-session --target $instanceId --region $region
```

---

## Checklist — Acceptance Criteria
- [ ] EC2 t3.micro launched with Amazon Linux 2023 AMI
- [ ] IAM instance profile attached (project-intelligent-ec2-role)
- [ ] No SSH key pair associated
- [ ] Security group: no inbound rules (outbound only for SSM/HTTPS)
- [ ] Instance ID saved to infra/ec2/instance-id.env
- [ ] SSM Session Manager access verified

---

## References
- [Amazon Linux 2023 AMI](https://docs.aws.amazon.com/linux/al2023/release-notes/relnotes-2023.html)
- [AWS SSM Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)

---

> Document last updated: 2026-05-12
