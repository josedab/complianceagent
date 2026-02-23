#!/bin/bash
# Add GitHub repository topics for discoverability
# Run this once after pushing to GitHub:
#
#   bash scripts/setup_github_topics.sh
#
# Requires: gh CLI authenticated

gh repo edit josedab/complianceagent \
  --add-topic compliance \
  --add-topic regulatory \
  --add-topic gdpr \
  --add-topic hipaa \
  --add-topic pci-dss \
  --add-topic soc2 \
  --add-topic ai-compliance \
  --add-topic eu-ai-act \
  --add-topic regtech \
  --add-topic devsecops \
  --add-topic fastapi \
  --add-topic nextjs \
  --add-topic copilot-sdk \
  --add-topic compliance-as-code

echo "✅ GitHub topics added. Visit https://github.com/josedab/complianceagent to verify."
