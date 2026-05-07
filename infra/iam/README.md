# IAM Policies Guide

Because AWS strictly requires IAM Policies to be valid JSON (which does not support comments), this file serves as the documentation for the `.json` files in this directory.

### 1. `ec2-instance-policy.json` (Issue #58)
**Attached to:** `project-intelligent-ec2-role`
**Purpose:** This is the exact list of permissions the EC2 virtual machine gets. 
- It allows reading/writing to `project-intelligent-*` S3 buckets.
- It allows querying `project-intelligent-*` DynamoDB tables.
- It allows accessing the AWS Glue Data Catalog (`glue:GetTable`, `glue:UpdateTable`, etc.) which is required to manage the schemas and metadata for our **Apache Iceberg** tables.
- It allows secure connection via AWS Systems Manager (SSM) so we don't need SSH keys.
- **Security:** Notice how it only allows access to specific `project-intelligent-*` resources. No wildcards (`*`) for resource names where possible!

### 2. `lambda-execution-policy.json` (Issue #59)
**Attached to:** `project-intelligent-lambda-role`
**Purpose:** This grants our Lambda function the exact permissions needed to trigger our batch jobs.
- It allows Lambda to run commands on our specific EC2 instance via SSM.
- It allows Lambda to write logs to CloudWatch so we can debug.
- **Security:** The `ssm:SendCommand` is strictly locked down to our specific EC2 instance. The Lambda cannot execute commands on any other servers in the account.

### 3. `ghactions-trust-policy.json` (Issue #60)
**Attached to:** `project-intelligent-ghactions-role` (Trust Relationship)
**Purpose:** This is the "OIDC Trust" policy. It tells AWS who is allowed to assume this role.
- It tells AWS: *"Trust GitHub Actions, but only if the request comes exactly from the `main` branch of the `biteberry/project-intelligent` repository."*
- **Security:** This prevents anyone from forking the repository and using their own GitHub Actions to deploy malicious code to our AWS account.

### 4. `ghactions-permission-policy.json` (Issue #60)
**Attached to:** `project-intelligent-ghactions-role` (Permissions)
**Purpose:** This tells AWS what GitHub is allowed to do once it is trusted and assumes the role.
- It allows uploading deployment artifacts to our S3 bucket.
- It allows updating the code of our specific Lambda function.
- **Security:** It is scoped only to the artifacts bucket and the project Lambda function. GitHub cannot delete our DynamoDB tables or alter our EC2 instance.

---

## 5. Provisioning the Roles via AWS CLI (Issue #61)

To automate the creation of these roles rather than manually clicking through the AWS Console, we use the AWS Command Line Interface (CLI). 

Here is the exact script and a step-by-step explanation of what each command does.

### A. Creating the EC2 Role
```powershell
aws iam create-role --role-name project-intelligent-ec2-role --assume-role-policy-document file://ec2-trust-policy.json
```
* **Explanation:** This creates the "blank badge" and attaches the Trust Policy so only an EC2 instance can use it.

```powershell
aws iam put-role-policy --role-name project-intelligent-ec2-role --policy-name ProjectIntelligentEC2Policy --policy-document file://ec2-instance-policy.json
```
* **Explanation:** This takes our custom JSON (`ec2-instance-policy.json`) and prints those specific S3/DynamoDB permissions onto the back of the badge.

```powershell
aws iam attach-role-policy --role-name project-intelligent-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
```
* **Explanation:** This attaches an AWS-managed policy. AWS provides this one out-of-the-box so that you can securely connect to the EC2 server later using Systems Manager (SSM) without needing SSH keys.

### B. Creating the Lambda Role
```powershell
aws iam create-role --role-name project-intelligent-lambda-role --assume-role-policy-document file://lambda-trust-policy.json
aws iam put-role-policy --role-name project-intelligent-lambda-role --policy-name ProjectIntelligentLambdaPolicy --policy-document file://lambda-execution-policy.json
aws iam attach-role-policy --role-name project-intelligent-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```
* **Explanation:** This repeats the exact same three steps as EC2, but uses the Lambda policies instead. The final command attaches the built-in AWS policy that allows Lambda to write basic logs to CloudWatch.

### C. Setting up GitHub Actions OIDC
```powershell
aws iam create-open-id-connect-provider --url "https://token.actions.githubusercontent.com" --client-id-list "sts.amazonaws.com" --thumbprint-list "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
```
* **Explanation:** Before we create the GitHub role, we have to tell AWS that "GitHub Actions" is a trusted external identity provider (OIDC). This command creates that trust link.

```powershell
aws iam create-role --role-name project-intelligent-ghactions-role --assume-role-policy-document file://ghactions-trust-policy.json
aws iam put-role-policy --role-name project-intelligent-ghactions-role --policy-name ProjectIntelligentGHActionsPolicy --policy-document file://ghactions-permission-policy.json
```
* **Explanation:** Once the OIDC provider is created, this creates the role specifically for GitHub Actions using the trust and permission policies we wrote.

### D. Saving the Output
At the very end, every role in AWS gets a unique Amazon Resource Name (ARN). These are saved into a file called `role-arns.env` in this directory so we can easily reference them when we build the actual infrastructure (like the EC2 instance) later.
