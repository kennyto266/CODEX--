# BMAD CI/CD Pipeline Guide

## 📋 Overview

This document describes the complete CI/CD (Continuous Integration/Continuous Deployment) pipeline for the BMAD (Batch Multi-Agent Director) quantitative trading system using GitHub Actions.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Repository                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Source     │  │   Feature    │  │   Release    │      │
│  │   Code       │  │   Branch     │  │   Branch     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼──────────────────┼──────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflows                 │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   docker-    │  │   helm-      │  │   k8s-       │      │
│  │   build      │  │   chart      │  │   deploy     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼──────────────────┼──────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Container Registry                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   ghcr.io    │  │   Helm       │  │   Security   │      │
│  │   Docker     │  │   Charts     │  │   Scans      │      │
│  │   Images     │  │              │  │              │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼──────────────────┼──────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   Kubernetes Clusters                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Staging    │  │  Production  │  │   Monitoring │      │
│  │   (auto)     │  │   (manual)   │  │   (prometheus│      │
│  │              │  │              │  │  grafana)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Workflows

### 1. Docker Build and Push (`docker-build.yaml`)

**Trigger Events:**
- Push to `main`, `feature/**`, `release/**` branches
- New tags (`v*.*.*`)
- Pull requests to `main`

**Jobs:**
- ✅ Code checkout
- ✅ Python 3.10 setup
- ✅ Dependencies installation with caching
- ✅ Test execution
- ✅ Docker image build and push (multi-architecture: amd64, arm64)
- ✅ SBOM (Software Bill of Materials) generation
- ✅ Security scanning with Trivy
- ✅ Cache optimization

**Output:**
- Docker image: `ghcr.io/<owner>/<repository>:<tag>`
- SBOM artifact
- Trivy scan results (SARIF format)

**Usage:**
```yaml
# Example workflow dispatch
gh workflow run docker-build.yaml
```

### 2. Helm Chart CI (`helm-chart.yaml`)

**Trigger Events:**
- Push to `main`, `feature/**`, `release/**` branches (only when `helm/` directory changes)
- Pull requests to `main` (only when `helm/` directory changes)

**Jobs:**
- ✅ Chart structure validation
- ✅ Helm linting
- ✅ Template rendering and preview
- ✅ Helm unit tests (optional)
- ✅ Chart packaging
- ✅ Chart publishing to GitHub Pages
- ✅ Security scanning (Trivy, Checkov)
- ✅ OCI registry publishing (on tags)

**Output:**
- Helm chart package: `bmad-1.0.0.tgz`
- GitHub Pages: `https://<owner>.github.io/<repository>/bmad-helm/`
- OCI registry: `oci://ghcr.io/<owner>/bmad`
- SARIF security reports

**Usage:**
```bash
# Install from GitHub Pages
helm repo add bmad https://<owner>.github.io/bmad-helm
helm install bmad bmad/bmad

# Install from OCI registry
helm registry login ghcr.io
helm install bmad oci://ghcr.io/<owner>/bmad --version 1.0.0
```

### 3. Kubernetes Deployment (`k8s-deploy.yaml`)

**Trigger Events:**
- Push to `main` branch (after Docker/Helm workflows complete)
- Workflow run completion

**Environments:**
- **Staging**: Automatic deployment for feature branches
- **Production**: Manual approval required for main branch

**Jobs:**
- ✅ Deployment validation
- ✅ kubectl and Helm setup
- ✅ Namespace creation
- ✅ Environment-specific values file generation
- ✅ Helm upgrade with `--wait` and `--atomic`
- ✅ Deployment verification
- ✅ Smoke tests
- ✅ Rollback on failure

**Staging Configuration:**
```yaml
apiServer:
  replicaCount: 1
  image:
    tag: "<sha>"

ingress:
  enabled: true
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"

secret:
  data:
    hkma_api_key: "${{ secrets.STAGING_HKMA_API_KEY }}"
```

**Production Configuration:**
```yaml
apiServer:
  replicaCount: 3
  image:
    tag: "<sha>"

ingress:
  enabled: true
  tls:
    enabled: true

secret:
  data:
    hkma_api_key: "${{ secrets.PRODUCTION_HKMA_API_KEY }}"
    csd_api_key: "${{ secrets.PRODUCTION_CSD_API_KEY }}"

postgresql:
  enabled: true
```

**Deployment URLs:**
- Staging: `https://staging-bmad.yourdomain.com`
- Production: `https://bmad.yourdomain.com`

### 4. Integrated CI/CD (`ci-cd.yaml`)

**Trigger Events:**
- Push to any branch
- Pull requests
- Tags (v*.*.*)

**Pipeline Stages:**
1. **CI Stage** (Code Quality)
   - Code formatting (Black)
   - Import sorting (isort)
   - Linting (flake8)
   - Type checking (mypy)
   - Security scanning (Bandit)
   - Test execution with coverage
   - Build application

2. **BUILD Stage** (Docker Images)
   - Multi-platform build
   - Security scanning
   - SBOM generation

3. **CHART Stage** (Helm Charts)
   - Linting and testing
   - Packaging

4. **SECURITY Stage** (SAST/DAST)
   - Trivy vulnerability scanning
   - CodeQL SAST
   - SARIF report upload

5. **DEPLOY Stage** (Kubernetes)
   - Production deployment
   - Health checks
   - Smoke tests

6. **NOTIFY Stage** (Notifications)
   - Success/failure notifications
   - Deployment summary

### 5. Local Development (`local-dev.yaml`)

**Trigger Events:**
- Manual workflow dispatch

**Purpose:**
- Deploy to local Docker Compose environment
- Run integration tests
- Verify functionality

**Usage:**
```bash
# Trigger manual deployment
gh workflow run local-dev.yaml -f environment=dev
```

## 🔐 Required Secrets

Configure these secrets in your GitHub repository:

### Container Registry
- `GITHUB_TOKEN` - Automatically available (no setup needed)

### Docker Hub (Optional)
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub access token

### Kubernetes Clusters

**Staging Cluster:**
- `KUBECONFIG_STAGING` - Base64-encoded kubeconfig for staging cluster

**Production Cluster:**
- `KUBECONFIG_PRODUCTION` - Base64-encoded kubeconfig for production cluster

### Application Secrets

**Staging Environment:**
- `STAGING_HKMA_API_KEY`
- `STAGING_CSD_API_KEY`
- `STAGING_JWT_SECRET`

**Production Environment:**
- `PRODUCTION_HKMA_API_KEY`
- `PRODUCTION_CSD_API_KEY`
- `PRODUCTION_ALPHA_VANTAGE_API_KEY`
- `PRODUCTION_JWT_SECRET`
- `PRODUCTION_REDIS_PASSWORD`
- `PRODUCTION_POSTGRES_PASSWORD`
- `PRODUCTION_DB_PASSWORD`

### Notifications
- `SLACK_WEBHOOK` - Slack webhook URL for notifications

## 🏷️ Image Tagging Strategy

The pipeline uses the following tagging strategy:

| Git Ref | Image Tag | Description |
|---------|-----------|-------------|
| `main` branch | `main-<sha>` | Latest from main |
| `feature/xyz` | `feature-xyz-<sha>` | Feature branch build |
| `release/v1.0.0` | `release-1.0.0-<sha>` | Release branch |
| Tag `v1.0.0` | `1.0.0`, `1.0`, `latest` | Semantic versioning |

## 📦 Artifact Management

### Uploaded Artifacts
- `helm-charts` - Packaged Helm charts
- `test-results` - Test execution results
- `coverage.xml` - Code coverage report
- `sbom-<sha>` - Software Bill of Materials
- `helm-index` - Helm repository index

### Retention
- Test artifacts: 30 days
- Helm charts: 30 days
- SBOM: Permanent (security requirement)
- Coverage reports: Permanent

## 🔍 Monitoring & Alerts

### Security Scanning
- **Trivy**: Container image vulnerabilities
- **Bandit**: Python security linting
- **CodeQL**: Static analysis
- **SARIF**: Uploaded to GitHub Security tab

### Deployment Monitoring
- Health check endpoint: `/health`
- API documentation: `/docs`
- Prometheus metrics: `/metrics`
- Integration tests

### Notifications
- Slack notifications on success/failure
- GitHub deployment status
- Email alerts (optional)

## 🚨 Rollback Strategy

### Automatic Rollback
Triggered when:
- Health checks fail
- Smoke tests fail
- Deployment verification fails

```yaml
rollback-on-failure:
  runs-on: ubuntu-latest
  if: failure()
  steps:
    - name: Rollback deployment
      run: |
        helm rollback <release-name> -n <namespace>
```

### Manual Rollback
```bash
# Rollback to previous version
helm rollback bmad-production -n bmad-production

# Rollback to specific revision
helm rollback bmad-production 2 -n bmad-production
```

## 🧪 Testing Strategy

### Test Types
1. **Unit Tests**: `pytest tests/unit/`
2. **Integration Tests**: `pytest tests/integration/`
3. **E2E Tests**: `pytest tests/e2e/`
4. **Smoke Tests**: Post-deployment health checks

### Coverage Requirements
- Minimum: 80%
- Tracked with: Codecov
- Reports: HTML and XML formats

## 📊 Performance Optimization

### Caching
- pip dependencies: `~/.cache/pip`
- Docker layers: GitHub Actions cache
- Helm repository: `~/.cache/helm/repository`

### Parallelization
- Build matrix: Multi-platform (amd64, arm64)
- Job dependencies: Optimized DAG

### Resource Limits
- Ubuntu runners: 2 CPU, 7GB RAM
- Timeout: 30 minutes (configurable)
- Retries: Automatic on transient failures

## 🎯 Best Practices

### Branching Strategy
- `main` - Production code, protected
- `feature/*` - Feature development
- `release/*` - Release preparation
- `hotfix/*` - Emergency fixes

### Pull Request Requirements
- ✅ All CI checks pass
- ✅ Code review approved
- ✅ Security scan passed
- ✅ Documentation updated

### Deployment Checklist
- [ ] Version bumped (if applicable)
- [ ] Secrets updated
- [ ] Helm chart tested
- [ ] Rollback plan verified
- [ ] Monitoring configured

## 📚 Additional Resources

### Documentation
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

### Tools
- Docker: Containerization
- Helm: Kubernetes package manager
- kubectl: Kubernetes CLI
- Trivy: Vulnerability scanner
- CodeQL: Code analysis

## 🆘 Troubleshooting

### Common Issues

**1. Deployment Timeout**
```
Error: timed out waiting for the condition
```
**Solution:** Increase timeout in Helm command
```bash
helm upgrade --install <release> <chart> --timeout=900s
```

**2. Image Pull Failed**
```
Error: ErrImagePull
```
**Solution:** Check image registry and authentication
```bash
# Verify login
docker login ghcr.io -u <username> -p <token>

# Check image exists
docker pull ghcr.io/<owner>/<repo>:<tag>
```

**3. Helm Chart Lint Failed**
```
Error: validation: chart metadata is missing
```
**Solution:** Verify Chart.yaml has required fields
```yaml
apiVersion: v2
name: bmad
version: 1.0.0
```

**4. kubectl Connection Failed**
```
Error: couldn't get server version: Get "https://...api": dial tcp: i/o timeout
```
**Solution:** Check kubeconfig and cluster accessibility
```bash
# Verify cluster connection
kubectl cluster-info

# Check context
kubectl config get-contexts
```

## 📞 Support

For issues or questions:
1. Check GitHub Actions logs
2. Review deployment logs in Kubernetes
3. Verify secrets and configuration
4. Consult troubleshooting section
5. Open GitHub issue

---

**Last Updated**: 2025-11-06
**Version**: 1.0.0
**Maintainer**: BMAD Development Team
