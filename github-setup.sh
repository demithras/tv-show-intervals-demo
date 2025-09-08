#!/bin/bash

# GitHub Actions Setup Helper
# This script provides instructions for setting up Neon integration

echo "🚀 GitHub Actions Setup for Neon Database Testing"
echo "=================================================="
echo ""

echo "📋 Prerequisites:"
echo "1. Neon account at https://neon.tech"
echo "2. GitHub repository with admin access"
echo "3. This repository pushed to GitHub"
echo ""

echo "🔧 Setup Steps:"
echo ""

echo "1️⃣  Get your Neon Project ID:"
echo "   - Go to https://console.neon.tech"
echo "   - Select your project"
echo "   - Copy the Project ID from the URL or dashboard"
echo ""

echo "2️⃣  Get your Neon API Key:"
echo "   - In Neon console, go to Account Settings → API Keys"
echo "   - Create a new API key"
echo "   - Copy the key (it will only be shown once)"
echo ""

echo "3️⃣  Add GitHub Repository Variables:"
echo "   - Go to your GitHub repository"
echo "   - Navigate to: Settings → Secrets and variables → Actions"
echo "   - Click 'Variables' tab"
echo "   - Add New Repository Variable:"
echo "     Name: NEON_PROJECT_ID"
echo "     Value: [Your Neon Project ID]"
echo ""

echo "4️⃣  Add GitHub Repository Secrets:"
echo "   - In the same page, click 'Secrets' tab"
echo "   - Add New Repository Secret:"
echo "     Name: NEON_API_KEY"
echo "     Value: [Your Neon API Key]"
echo ""

echo "5️⃣  Test the Setup:"
echo "   - Create a new branch: git checkout -b test-ci"
echo "   - Make a small change and commit it"
echo "   - Push and create a Pull Request"
echo "   - The GitHub Action should automatically:"
echo "     • Create a Neon database branch"
echo "     • Run the schema migration"
echo "     • Execute all BDD tests"
echo "     • Post results as PR comments"
echo ""

echo "✅ That's it! Your repository now has automated database testing on every PR."
echo ""

echo "🔍 Troubleshooting:"
echo "   - Check the Actions tab for detailed logs"
echo "   - Ensure your Neon project has sufficient resources"
echo "   - Verify the API key has the correct permissions"
echo ""

echo "📚 For more details, see the README.md file."