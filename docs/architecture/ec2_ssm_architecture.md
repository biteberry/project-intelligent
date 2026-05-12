# EC2 + SSM Architecture for Orchestration

## Overview
- EC2 instance is managed via AWS Systems Manager (SSM), not SSH.
- IAM instance profile is required for SSM and pipeline permissions.

## Key Components
- EC2 instance (t3.micro, Amazon Linux 2023)
- IAM instance profile (project-intelligent-ec2-profile)
- IAM role (project-intelligent-ec2-role)
- SSM agent (pre-installed on Amazon Linux 2023)

## Flow
1. Launch EC2 with instance profile attached
2. SSM agent registers instance for remote management
3. Lambda SSM dispatcher triggers SSM RunCommand to EC2

## Security
- No SSH key pair
- Security group: no inbound rules
- All access via SSM Session Manager

## References
- See implementation guide: docs/implementation/issue-44-iam-instance-profile-guide.md
