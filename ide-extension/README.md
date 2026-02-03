# IDE Extension Development

This guide covers developing and building the ComplianceAgent IDE extensions.

## Overview

ComplianceAgent provides IDE extensions that bring real-time compliance analysis directly into your development environment. Currently supported:

| IDE | Status | Location |
|-----|--------|----------|
| VS Code | ✅ Available | `ide-extension/vscode/` |
| JetBrains | 🚧 Planned | - |
| Neovim | 🚧 Planned | - |

## VS Code Extension

### Features

- **Real-time compliance scanning** as you type
- **25+ compliance patterns** for GDPR, HIPAA, PCI-DSS, SOC 2, EU AI Act
- **AI-powered quick fixes** with one-click application
- **Team suppressions** synchronized across the organization
- **Learning system** that improves from feedback

### Development Setup

```bash
cd ide-extension/vscode

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Watch mode (for development)
npm run watch
```

### Running in Development

1. Open the `ide-extension/vscode` folder in VS Code
2. Press `F5` to launch the Extension Development Host
3. The extension will be active in the new VS Code window

### Project Structure

```
ide-extension/vscode/
├── src/
│   ├── extension.ts      # Extension entry point
│   ├── languageServer.ts # Compliance analysis logic
│   ├── quickFix.ts       # Quick fix provider
│   ├── commands.ts       # Command implementations
│   ├── config.ts         # Configuration handling
│   └── api.ts            # Backend API client
├── package.json          # Extension manifest
└── tsconfig.json         # TypeScript config
```

### Extension Configuration

The extension exposes these settings:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `complianceagent.apiEndpoint` | string | `https://api.complianceagent.ai` | Backend API URL |
| `complianceagent.apiKey` | string | - | API key from dashboard |
| `complianceagent.enableRealTimeScanning` | boolean | `true` | Enable as-you-type scanning |
| `complianceagent.frameworks` | array | All | Frameworks to check |
| `complianceagent.severityThreshold` | string | `medium` | Minimum severity to show |
| `complianceagent.enableAIFixes` | boolean | `true` | Enable AI-powered fixes |
| `complianceagent.enableTeamSuppressions` | boolean | `true` | Sync team suppressions |
| `complianceagent.scanDebounceMs` | number | `1000` | Debounce time for scanning |

### Commands

| Command | Description |
|---------|-------------|
| `complianceagent.scanFile` | Scan current file |
| `complianceagent.scanWorkspace` | Scan entire workspace |
| `complianceagent.showDashboard` | Open compliance dashboard |
| `complianceagent.aiQuickFix` | Generate AI fix for selected code |
| `complianceagent.aiFixAll` | Fix all issues in file |
| `complianceagent.suppress` | Suppress current issue |
| `complianceagent.requestTeamSuppression` | Request team-wide suppression |
| `complianceagent.viewRuleStats` | View rule statistics |

### Building for Production

```bash
# Create .vsix package
npm run package

# This creates complianceagent-vscode-x.x.x.vsix
```

### Publishing

```bash
# Login to VS Code Marketplace
npx vsce login complianceagent

# Publish
npx vsce publish
```

### Testing

```bash
# Run unit tests
npm test

# Run integration tests (requires Extension Development Host)
npm run test:integration
```

## Backend API Integration

The extension communicates with these backend endpoints:

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/ide/analyze` | Analyze document for issues |
| `POST /api/v1/ide/quickfix` | Get AI-generated fix |
| `POST /api/v1/ide/deep-analyze` | Deep analysis of code block |
| `GET /api/v1/ide/suppressions` | Get team suppressions |
| `POST /api/v1/ide/suppressions` | Request new suppression |
| `POST /api/v1/ide/feedback` | Submit feedback on detection |
| `GET /api/v1/ide/stats/rules` | Get rule statistics |

### API Authentication

The extension uses API key authentication:

```typescript
const response = await fetch(`${apiEndpoint}/api/v1/ide/analyze`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${apiKey}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    uri: document.uri.toString(),
    content: document.getText(),
    language: document.languageId,
    regulations: enabledFrameworks,
  }),
});
```

## Compliance Patterns

The extension detects these pattern categories:

### GDPR (6 patterns)
- PII handling without encryption
- Personal data in logs
- Missing consent checks
- Missing data retention
- Cross-border transfers
- Missing deletion handlers

### HIPAA (4 patterns)
- PHI without encryption
- Healthcare data in logs
- Missing access controls
- Missing audit logging

### PCI-DSS (5 patterns)
- Card number handling
- CVV storage
- Encryption keys in code
- Card data in logs
- Unmasked card display

### SOC 2 (4 patterns)
- Missing encryption
- Missing access logging
- Hardcoded secrets
- Insecure data handling

### EU AI Act (3 patterns)
- Bias detection issues
- Missing explainability
- Data quality concerns

## Adding New Patterns

To add a new compliance pattern:

```typescript
// src/patterns.ts
export const COMPLIANCE_PATTERNS: CompliancePattern[] = [
  // Existing patterns...
  
  // Add new pattern
  {
    id: 'CUSTOM-001',
    framework: 'CustomFramework',
    severity: DiagnosticSeverity.Warning,
    pattern: /sensitivePattern/g,
    message: 'Custom compliance issue detected',
    codeDescription: {
      href: 'https://docs.example.com/requirement'
    },
    recommendation: 'Apply recommended fix...',
    languages: ['python', 'javascript', 'typescript'],
  },
];
```

## Resources

- [VS Code Extension API](https://code.visualstudio.com/api)
- [Language Server Protocol](https://microsoft.github.io/language-server-protocol/)
- [VS Code Extension Guidelines](https://code.visualstudio.com/api/references/extension-guidelines)

## Related Documentation

- [IDE Linting Feature Guide](../docs/features/ide-linting.md) - User documentation
- [API Reference](../docs/api/reference.md) - Backend API docs
