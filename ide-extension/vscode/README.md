# ComplianceAgent VS Code Extension

Real-time compliance suggestions and quick-fixes for regulated codebases.

## Features

- **Real-time Scanning**: Automatically scans code as you type for compliance issues
- **Multiple Frameworks**: Supports GDPR, HIPAA, SOC 2, PCI-DSS, and more
- **Quick Fixes**: One-click fixes for common compliance issues
- **Dashboard**: Visual overview of compliance status
- **Configurable**: Set severity thresholds and framework preferences

## Installation

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "ComplianceAgent"
4. Click Install

Or install via command line:
```bash
code --install-extension complianceagent.complianceagent-vscode
```

## Configuration

Open Settings (Ctrl+,) and search for "ComplianceAgent":

- **API Endpoint**: Your ComplianceAgent server URL
- **API Key**: Your API key from the ComplianceAgent dashboard
- **Enable Real-Time Scanning**: Toggle real-time analysis
- **Frameworks**: Select which frameworks to check
- **Severity Threshold**: Minimum severity to display

## Commands

- `ComplianceAgent: Scan Current File` - Scan the active file
- `ComplianceAgent: Scan Workspace` - Scan all files in workspace
- `ComplianceAgent: Show Dashboard` - Open compliance dashboard
- `ComplianceAgent: Configure` - Open settings

## Supported Languages

- Python
- JavaScript/TypeScript
- Java
- Go

## Development

```bash
cd ide-extension/vscode
npm install
npm run compile
```

Press F5 to launch Extension Development Host.

## License

MIT
