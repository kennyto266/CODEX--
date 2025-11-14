#!/bin/bash
set -e

echo "======================================"
echo "API Documentation Deployment Script"
echo "======================================"
echo ""

# Configuration
DOCS_DIR="${1:-docs}"
GITHUB_REPO="${2:-$(git remote get-url origin 2>/dev/null | sed 's/.*:\/\/github\.com\///' | sed 's/\.git$//' || echo '')}"
BRANCH="${3:-main}"
COMMIT_MESSAGE="${4:-docs: Update API documentation $(date +%Y-%m-%d)}"

if [ -z "$GITHUB_REPO" ]; then
    echo "❌ Error: Could not determine GitHub repository"
    echo "Usage: ./deploy_docs.sh [docs_dir] [repo] [branch] [commit_message]"
    exit 1
fi

echo "📁 Documentation directory: $DOCS_DIR"
echo "📦 GitHub repository: $GITHUB_REPO"
echo "🌿 Branch: $BRANCH"
echo "💬 Commit message: $COMMIT_MESSAGE"
echo ""

# Check if docs directory exists
if [ ! -d "$DOCS_DIR" ]; then
    echo "❌ Error: Documentation directory '$DOCS_DIR' not found"
    echo "Run 'python scripts/generate_api_docs.py' first"
    exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI (gh) not installed"
    echo "Please install it from: https://cli.github.com/"
    echo ""
    echo "Alternative: Manual deployment instructions"
    echo "1. Copy $DOCS_DIR to your repository's gh-pages branch"
    echo "2. Enable GitHub Pages in repository settings"
    echo "3. Select 'Deploy from a branch' -> 'gh-pages'"
    exit 1
fi

# Ensure git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository"
    echo "Please run this script from the root of your git repository"
    exit 1
fi

echo "🔄 Deploying to GitHub Pages..."
echo ""

# Check if gh-pages branch exists
if ! git show-ref --verify --quiet refs/heads/gh-pages; then
    echo "📄 Creating gh-pages branch..."
    git checkout --orphan gh-pages
    git rm -rf . > /dev/null 2>&1 || true
    echo "Documentation deployment" > README.md
    git add README.md
    git commit -m "Initial gh-pages branch" > /dev/null 2>&1
    git push origin gh-pages --set-upstream > /dev/null 2>&1
    git checkout - > /dev/null 2>&1
    echo "✅ Created gh-pages branch"
else
    echo "✅ gh-pages branch exists"
fi

# Deploy docs
echo ""
echo "📤 Uploading documentation..."

# Create a temporary directory for deployment
TEMP_DIR=$(mktemp -d)
cp -r "$DOCS_DIR"/* "$TEMP_DIR/"

# Add CNAME if custom domain is configured
if [ -f "docs/CNAME" ]; then
    cp docs/CNAME "$TEMP_DIR/"
fi

# Add .nojekyll to disable Jekyll processing
touch "$TEMP_DIR/.nojekyll"

# Create version file
echo "{\"version\": \"$(git rev-parse HEAD 2>/dev/null || echo 'unknown')\", \"deployed\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > "$TEMP_DIR/VERSION.json"

# Deploy using gh CLI
cd "$TEMP_DIR"
git init
git config user.name "GitHub Actions"
git config user.email "actions@github.com"

# Add all files
git add .

# Commit
git commit -m "$COMMIT_MESSAGE"

# Force push to gh-pages
git push -f origin gh-pages:gh-pages > /dev/null 2>&1

# Cleanup
cd - > /dev/null
rm -rf "$TEMP_DIR"

echo ""
echo "✅ Documentation deployed successfully!"
echo ""
echo "🌐 Your documentation is available at:"
echo "   https://$GITHUB_REPO.github.io"
echo ""
echo "📋 Deployment Summary:"
echo "   • Branch: gh-pages"
echo "   • Files deployed: $(find $DOCS_DIR -type f | wc -l)"
echo "   • Commit: $COMMIT_MESSAGE"
echo ""

# Create a simple deployment log
DEPLOY_LOG=".deployment_log"
echo "$(date +%Y-%m-%dT%H:%M:%SZ) - $GITHUB_REPO - $COMMIT_MESSAGE" >> "$DEPLOY_LOG"
echo "📝 Deployment logged to $DEPLOY_LOG"

# Generate search index
if [ -f "$DOCS_DIR/search.json" ]; then
    echo ""
    echo "🔍 Search index available at: https://$GITHUB_REPO.github.io/search.json"
fi

echo ""
echo "======================================"
echo "Deployment Complete!"
echo "======================================"
