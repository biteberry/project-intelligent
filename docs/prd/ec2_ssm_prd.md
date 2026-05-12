# PRD: EC2 + SSM Orchestration

## Purpose
Enable secure, automated orchestration of pipeline workloads on EC2 using AWS SSM and Lambda.

## Requirements
- EC2 instance must be SSM-managed (no SSH)
- IAM instance profile must be attached
- Lambda SSM dispatcher must be able to trigger SSM RunCommand

## Acceptance Criteria
- EC2 instance launches with IAM instance profile
- SSM agent is active and instance is visible in SSM
- No SSH key, no inbound security group rules

## References
- Architecture: docs/architecture/ec2_ssm_architecture.md
- Implementation: docs/implementation/issue-44-iam-instance-profile-guide.md
