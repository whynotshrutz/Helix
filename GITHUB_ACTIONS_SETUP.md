# GitHub Actions Setup for AWS Deployment

## Problem

Your temporary AWS credentials won't work with GitHub Actions because:
1. They expire quickly (usually 1-12 hours)
2. GitHub Actions needs long-lived credentials
3. Session tokens aren't stored in GitHub Secrets

## Solution: Set Up GitHub Secrets

### Step 1: Get Permanent AWS Credentials

You need **IAM User credentials** (not temporary session credentials).

#### Option A: Create New IAM User (Recommended)

1. **Go to AWS Console** → IAM → Users
2. **Create User:**
   - Username: `github-actions-helix`
   - Access type: ✅ Programmatic access
3. **Attach Policies:**
   - `AmazonEC2ContainerRegistryPowerUser`
   - `AmazonEKSClusterPolicy` (or custom policy)
4. **Download Credentials:**
   - Save `aws_access_key_id` (starts with AKIA...)
   - Save `aws_secret_access_key`

#### Option B: Use Your Existing IAM User

If you have permanent credentials (not the temporary ones you showed):

```bash
# Check your AWS config
cat ~/.aws/credentials

# Should show something like:
[default]
aws_access_key_id = AKIA...
aws_secret_access_key = ...
```

**Important:** Don't use the credentials you shared (they start with ASIA... and have a session token - those are temporary!)

### Step 2: Add Secrets to GitHub

1. **Go to GitHub Repository:**
   - Navigate to: https://github.com/whynotshrutz/Helix

2. **Open Settings:**
   - Click "Settings" tab
   - Click "Secrets and variables" → "Actions"

3. **Add New Repository Secrets:**

   Click "New repository secret" and add each of these:

   **Secret 1: AWS_ACCESS_KEY_ID**
   ```
   Name: AWS_ACCESS_KEY_ID
   Value: AKIA... (your permanent access key)
   ```

   **Secret 2: AWS_SECRET_ACCESS_KEY**
   ```
   Name: AWS_SECRET_ACCESS_KEY
   Value: (your secret access key)
   ```

   **Secret 3: AWS_ACCOUNT_ID**
   ```
   Name: AWS_ACCOUNT_ID
   Value: 007727117492
   ```

   **Secret 4: NVIDIA_API_KEY** (if using CI/CD for deployment)
   ```
   Name: NVIDIA_API_KEY
   Value: (your NVIDIA API key from build.nvidia.com)
   ```

   **Secret 5: GITHUB_TOKEN** (GitHub personal access token)
   ```
   Name: GH_TOKEN
   Value: (your GitHub personal access token)
   ```

### Step 3: Create IAM Policy for GitHub Actions

The IAM user needs specific permissions. Create a custom policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRPermissions",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:CreateRepository",
        "ecr:DescribeRepositories"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EKSPermissions",
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:UpdateClusterConfig"
      ],
      "Resource": "arn:aws:eks:us-east-1:007727117492:cluster/helix-cluster"
    },
    {
      "Sid": "K8sPermissions",
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

**To Apply:**
1. AWS Console → IAM → Policies → Create Policy
2. Paste JSON above
3. Name it: `GitHubActionsHelixPolicy`
4. Attach to `github-actions-helix` user

### Step 4: Update EKS ConfigMap (Allow GitHub Actions User)

GitHub Actions needs access to your EKS cluster:

```bash
# Get current config
kubectl get configmap aws-auth -n kube-system -o yaml > aws-auth.yaml

# Edit aws-auth.yaml and add:
```

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapUsers: |
    - userarn: arn:aws:iam::007727117492:user/github-actions-helix
      username: github-actions
      groups:
        - system:masters
```

```bash
# Apply the updated config
kubectl apply -f aws-auth.yaml
```

### Step 5: Test GitHub Actions

1. **Commit and Push:**
   ```bash
   git add .github/workflows/deploy.yml
   git commit -m "Update GitHub Actions workflow for AWS credentials"
   git push origin main
   ```

2. **Check Workflow:**
   - Go to: https://github.com/whynotshrutz/Helix/actions
   - Watch the workflow run
   - Should see green checkmarks if successful

### Step 6: Trigger Manual Deployment

```bash
# From GitHub UI:
# 1. Go to Actions tab
# 2. Select "Deploy to AWS EKS" workflow
# 3. Click "Run workflow"
# 4. Select branch: main
# 5. Click green "Run workflow" button

# Or push a tag:
git tag v1.0.0
git push origin v1.0.0
```

## Alternative: Use OIDC (More Secure)

If you want better security (no long-lived credentials), use OIDC:

### Create IAM Role for GitHub

1. **AWS Console → IAM → Roles → Create Role**
2. **Trusted Entity:** Web identity
3. **Identity Provider:** 
   - Provider: `token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`
4. **Add Condition:**
   ```json
   {
     "StringEquals": {
       "token.actions.githubusercontent.com:sub": "repo:whynotshrutz/Helix:ref:refs/heads/main"
     }
   }
   ```
5. **Attach Policies:** Same as above
6. **Name Role:** `GitHubActionsHelixRole`
7. **Copy Role ARN:** `arn:aws:iam::007727117492:role/GitHubActionsHelixRole`

### Update GitHub Workflow for OIDC

Update `.github/workflows/deploy.yml`:

```yaml
jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # Required for OIDC
      contents: read
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::007727117492:role/GitHubActionsHelixRole
          aws-region: us-east-1
```

### Add Secret to GitHub

```
Name: AWS_ROLE_ARN
Value: arn:aws:iam::007727117492:role/GitHubActionsHelixRole
```

## Current Status

✅ **Workflow Updated:** Now uses AWS access keys (simpler)
⏳ **Secrets Needed:** Add to GitHub repository settings
⏳ **IAM User:** Create permanent IAM user for GitHub Actions
⏳ **EKS Access:** Update aws-auth configmap

## Quick Setup Commands

```bash
# 1. Create IAM user (AWS Console or CLI)
aws iam create-user --user-name github-actions-helix

# 2. Create access keys
aws iam create-access-key --user-name github-actions-helix
# Save the output!

# 3. Attach policies
aws iam attach-user-policy \
  --user-name github-actions-helix \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

# 4. Add to GitHub secrets (via GitHub UI)
# AWS_ACCESS_KEY_ID
# AWS_SECRET_ACCESS_KEY
# AWS_ACCOUNT_ID

# 5. Update EKS access
kubectl edit configmap aws-auth -n kube-system
# Add the mapUsers section from above

# 6. Push and test
git push origin main
```

## Troubleshooting

### Error: "Credentials could not be loaded"
- ✅ Check secrets are added to GitHub (Settings → Secrets)
- ✅ Secret names match exactly: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- ✅ Access keys are permanent (AKIA...), not temporary (ASIA...)

### Error: "AccessDenied" or "UnauthorizedOperation"
- ✅ IAM user has required policies attached
- ✅ Check policy JSON for correct permissions

### Error: "You must be logged in to the server (Unauthorized)"
- ✅ Update EKS aws-auth configmap with IAM user ARN
- ✅ Wait a few minutes for changes to propagate

### Error: "Repository does not exist"
- ✅ Run `scripts/build-and-push.sh` once locally to create ECR repositories
- ✅ Or add ECR repo creation to workflow

## Security Best Practices

1. **Use OIDC** (more secure, no long-lived credentials)
2. **Rotate access keys** every 90 days
3. **Use least privilege** (minimal IAM permissions)
4. **Enable MFA** on AWS account
5. **Monitor CloudTrail** for API calls
6. **Use separate AWS accounts** for dev/prod

## Summary

**What You Need to Do:**

1. ✅ Create permanent IAM user: `github-actions-helix`
2. ✅ Get access keys (AKIA... format)
3. ✅ Add secrets to GitHub repository
4. ✅ Update EKS aws-auth configmap
5. ✅ Push code to trigger workflow

**Then GitHub Actions will automatically:**
- Build Docker images
- Push to ECR
- Deploy to EKS
- Update running pods

---

**Your GitHub Actions workflow is now configured to use access keys! Just add the secrets and you're ready to deploy! 🚀**
