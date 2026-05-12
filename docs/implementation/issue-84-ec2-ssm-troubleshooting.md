# EC2 SSM Registration Troubleshooting Guide

If your EC2 instance does not appear in SSM (describe-instance-information returns empty), follow these steps:

---

## 1. Verify IAM Role and Policies
- The instance profile attached to your EC2 must have a role with the `AmazonSSMManagedInstanceCore` policy.
- Check the role:
  ```powershell
  aws ec2 describe-instances --instance-ids <your-instance-id> --query "Reservations[0].Instances[0].IamInstanceProfile.Arn" --output text --region <region>
  ```
- Check the attached policies:
  ```powershell
  aws iam list-attached-role-policies --role-name <your-role-name>
  ```
- If missing, attach the policy:
  ```powershell
  aws iam attach-role-policy --role-name <your-role-name> --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
  ```

---

## 2. Confirm Instance Profile Attachment
- The instance must be launched with the correct instance profile (not just the role).
- If you need to attach a profile to a running instance:
  ```powershell
  aws ec2 associate-iam-instance-profile --instance-id <your-instance-id> --iam-instance-profile Name=project-intelligent-ec2-profile --region <region>
  ```

---

## 3. Check SSM Agent Status
- Amazon Linux 2023: SSM agent is pre-installed and enabled by default.
- For other AMIs, connect via EC2 console or SSM (if possible) and run:
  ```bash
  sudo systemctl status amazon-ssm-agent
  sudo systemctl start amazon-ssm-agent
  sudo systemctl enable amazon-ssm-agent
  ```

---

## 4. Ensure Outbound Internet Access
- SSM agent needs to reach AWS endpoints. Your instance must have outbound access (public subnet or NAT gateway).
- Security group: allow all outbound traffic.
- Subnet route table: must have a route to an internet gateway or NAT gateway.

---

## 5. Wait and Re-Check
- It can take a few minutes for SSM registration after fixing the above.
- Re-run:
  ```powershell
  aws ssm describe-instance-information --region <region>
  ```

---

## 6. AWS Console Checks
- Go to Systems Manager > Fleet Manager > Managed Instances. Your instance should appear.
- If not, review the IAM, networking, and agent status again.

---

> Document last updated: 2026-05-13
