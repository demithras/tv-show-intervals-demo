#!/bin/bash

# Script to generate a comprehensive global index page for all PR test reports
# This script discovers existing PR reports and creates a unified index page

echo "🔍 Starting global index generation..."

REPO_OWNER="${1:-demithras}"
REPO_NAME="${2:-tv-show-intervals-demo}"
CURRENT_PR="${3:-}"
CURRENT_RUN="${4:-}"
CURRENT_BRANCH="${5:-}"
GITHUB_TOKEN="${6:-}"

BASE_URL="https://${REPO_OWNER}.github.io/${REPO_NAME}"
CURRENT_TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")

echo "📋 Repository: ${REPO_OWNER}/${REPO_NAME}"
echo "🌐 Base URL: ${BASE_URL}"
echo "⏰ Current timestamp: ${CURRENT_TIMESTAMP}"

# Create output directory
mkdir -p global-history

# Discover existing PR reports
echo "🔍 Discovering existing PR reports..."
EXISTING_PRS=""
PR_COUNT=0

# Check for existing PR directories by testing common PR numbers (1-20)
for PR_NUM in {1..20}; do
    echo "  🔍 Checking PR #${PR_NUM}..."
    
    # Check if PR report exists
    if curl -f -s -I "${BASE_URL}/pr-${PR_NUM}/" >/dev/null 2>&1; then
        echo "  ✅ Found PR #${PR_NUM} report"
        ((PR_COUNT++))
        
        # Try to get metadata from environment.properties
        BRANCH_NAME="unknown"
        RUN_NUMBER="unknown"
        TIMESTAMP_VALUE="unknown"
        
        if curl -f -s "${BASE_URL}/pr-${PR_NUM}/environment.properties" -o "/tmp/env-${PR_NUM}.properties" 2>/dev/null; then
            BRANCH_NAME=$(grep "^Branch.Name=" "/tmp/env-${PR_NUM}.properties" | cut -d'=' -f2 | tr -d '\r\n' || echo "unknown")
            RUN_NUMBER=$(grep "^Run.Number=" "/tmp/env-${PR_NUM}.properties" | cut -d'=' -f2 | tr -d '\r\n' || echo "unknown")
            TIMESTAMP_VALUE=$(grep "^Timestamp=" "/tmp/env-${PR_NUM}.properties" | cut -d'=' -f2 | tr -d '\r\n' || echo "unknown")
            
            echo "    📊 Branch: ${BRANCH_NAME}, Run: ${RUN_NUMBER}, Time: ${TIMESTAMP_VALUE}"
            rm -f "/tmp/env-${PR_NUM}.properties"
        else
            echo "    ⚠️ No environment.properties found for PR #${PR_NUM}"
        fi
        
        # Add special indicator for current PR
        CURRENT_INDICATOR=""
        if [ "${PR_NUM}" = "${CURRENT_PR}" ]; then
            CURRENT_INDICATOR=" - Latest Run ✨"
        fi
        
        EXISTING_PRS="${EXISTING_PRS}
                <a href=\"pr-${PR_NUM}/\" class=\"pr-link\">
                    📋 PR #${PR_NUM}${CURRENT_INDICATOR}
                    <div class=\"timestamp\">Run #${RUN_NUMBER} • ${BRANCH_NAME} • ${TIMESTAMP_VALUE}</div>
                </a>"
    else
        echo "    ❌ No report found for PR #${PR_NUM}"
    fi
done

echo "📊 Found ${PR_COUNT} existing PR reports"

# If no existing PRs found and we have current PR info, add it
if [ ${PR_COUNT} -eq 0 ] && [ -n "${CURRENT_PR}" ]; then
    echo "⚠️ No existing PRs found, adding current PR #${CURRENT_PR}"
    EXISTING_PRS="
                <a href=\"pr-${CURRENT_PR}/\" class=\"pr-link\">
                    📋 PR #${CURRENT_PR} - Latest Run ✨
                    <div class=\"timestamp\">Run #${CURRENT_RUN} • ${CURRENT_BRANCH} • ${CURRENT_TIMESTAMP}</div>
                </a>"
    PR_COUNT=1
fi

# Generate the HTML index page
echo "📝 Generating HTML index page..."

cat > global-history/index.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Test History - TV Show Intervals Demo</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; 
            margin: 40px; 
            background-color: #fafbfc;
            color: #24292e;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px; 
            border-radius: 12px; 
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 {
            margin: 0 0 10px 0;
            font-size: 2.2em;
        }
        .header p {
            margin: 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .stats {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 1px solid #e1e4e8;
        }
        .pr-link { 
            display: block; 
            padding: 15px; 
            margin: 10px 0; 
            background: white; 
            border-left: 4px solid #0366d6; 
            text-decoration: none; 
            color: #0366d6; 
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid #e1e4e8;
            transition: all 0.2s ease;
        }
        .pr-link:hover { 
            background: #f6f8fa; 
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            transform: translateY(-1px);
        }
        .pr-link .title {
            font-weight: 600;
            font-size: 1.1em;
            margin-bottom: 5px;
        }
        .timestamp { 
            color: #586069; 
            font-size: 0.9em; 
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .features {
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 1px solid #e1e4e8;
        }
        .features h2 {
            margin-top: 0;
            color: #24292e;
        }
        .features ul {
            list-style: none;
            padding: 0;
        }
        .features li {
            padding: 8px 0;
            border-bottom: 1px solid #eaecef;
        }
        .features li:last-child {
            border-bottom: none;
        }
        .badge {
            background: #28a745;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #586069;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 TV Show Intervals Demo - Test History</h1>
        <p>Comprehensive test reports and historical analysis for all pull requests</p>
    </div>
    
    <div class="stats">
        <h3>📊 Report Statistics</h3>
        <p><strong>${PR_COUNT}</strong> Pull Request reports available • Last updated: <strong>${CURRENT_TIMESTAMP}</strong></p>
    </div>
    
    <h2>📋 Available Test Reports</h2>
    <div id="reports">${EXISTING_PRS}
    </div>
    
    <div class="features">
        <h2>🔍 Report Features</h2>
        <ul>
            <li>📈 <strong>Trends & History</strong>: Track test execution performance and stability over time</li>
            <li>🎯 <strong>BDD Scenarios</strong>: Gherkin features with step-by-step execution details</li>
            <li>📊 <strong>Analytics & Insights</strong>: Test distribution, timing analysis, and failure patterns</li>
            <li>📎 <strong>Rich Attachments</strong>: Database queries, program data, logs, and debug information</li>
            <li>🏷️ <strong>Smart Categories</strong>: Organized by features, test types, and failure classifications</li>
            <li>🔄 <strong>Retry Analysis</strong>: Flaky test detection and retry pattern analysis</li>
            <li>⏱️ <strong>Duration Tracking</strong>: Performance trends and execution time optimization</li>
        </ul>
    </div>
    
    <div class="footer">
        <p>🤖 Generated automatically by GitHub Actions • <a href="https://github.com/${REPO_OWNER}/${REPO_NAME}" target="_blank">View Repository</a></p>
    </div>
</body>
</html>
EOF

echo "✅ Global index page generated successfully!"
echo "📊 Included ${PR_COUNT} PR reports"
echo "📁 Output: global-history/index.html"

# Show preview of generated content
echo ""
echo "📋 Generated index includes:"
if [ ${PR_COUNT} -gt 0 ]; then
    echo "${EXISTING_PRS}" | grep -o "PR #[0-9]*" | sort -u | sed 's/^/  ✅ /'
else
    echo "  ⚠️ No PR reports found"
fi

echo ""
echo "🏁 Global index generation completed!"