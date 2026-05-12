# Step-by-Step Checklist (Issue #155)

## 1. Create the IAM Instance Profile
```powershell
aws iam create-instance-profile --instance-profile-name project-intelligent-ec2-profile
```

## 2. Attach the EC2 Role to the Instance Profile
```powershell
aws iam add-role-to-instance-profile --instance-profile-name project-intelligent-ec2-profile --role-name project-intelligent-ec2-role
```

## 3. Verify the Instance Profile Exists
```powershell
aws iam list-instance-profiles --query "InstanceProfiles[*].InstanceProfileName" --output text
```
You should see `project-intelligent-ec2-profile` in the output.

## 4. Use in EC2 Launch Command
Use `project-intelligent-ec2-profile` as the value for `--iam-instance-profile Name=...` in your EC2 launch command.

---
# Issue #44 — Create IAM Instance Profile for EC2

This guide explains how to create an IAM instance profile and attach your EC2 role for SSM-managed compute.

---

## Step 1 — Create the Instance Profile
```powershell
aws iam create-instance-profile --instance-profile-name project-intelligent-ec2-profile
```

---

## Step 2 — Attach the Role to the Instance Profile
```powershell
aws iam add-role-to-instance-profile --instance-profile-name project-intelligent-ec2-profile --role-name project-intelligent-ec2-role
```
- Replace `project-intelligent-ec2-role` with your actual role name if different.

---

## Step 3 — Verify
```powershell
aws iam list-instance-profiles --query "InstanceProfiles[*].InstanceProfileName" --output text
```
- You should see `project-intelligent-ec2-profile` in the output.

---

## Usage
- Use `project-intelligent-ec2-profile` as the value for `--iam-instance-profile Name=...` in your EC2 launch command.

---

> Document last updated: 2026-05-12
