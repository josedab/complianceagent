"""Language Server Protocol server for ComplianceAgent IDE integration."""

import asyncio
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

from app.services.ide.analyzer import IDEComplianceAnalyzer
from app.services.ide.diagnostic import DiagnosticSeverity


if TYPE_CHECKING:
    from collections.abc import Callable


logger = structlog.get_logger()


@dataclass
class TextDocumentItem:
    """Represents an open text document."""

    uri: str
    language_id: str
    version: int
    text: str


@dataclass
class LSPServerConfig:
    """Configuration for the LSP server."""

    enabled_regulations: list[str] = field(default_factory=lambda: ["GDPR", "CCPA", "HIPAA", "EU AI Act"])
    severity_threshold: DiagnosticSeverity = DiagnosticSeverity.HINT
    analyze_on_open: bool = True
    analyze_on_change: bool = True
    analyze_on_save: bool = True
    debounce_ms: int = 500  # Debounce for on-change analysis


class ComplianceLSPServer:
    """Language Server Protocol implementation for compliance checking.

    This server provides real-time compliance diagnostics to IDE extensions
    using the standard LSP protocol.
    """

    def __init__(self, config: LSPServerConfig | None = None):
        self.config = config or LSPServerConfig()
        self.analyzer = IDEComplianceAnalyzer(
            enabled_regulations=self.config.enabled_regulations,
            severity_threshold=self.config.severity_threshold,
        )
        self.documents: dict[str, TextDocumentItem] = {}
        self._debounce_tasks: dict[str, asyncio.Task] = {}
        self._initialized = False
        self._shutdown_requested = False

        # LSP method handlers
        self._handlers: dict[str, Callable] = {
            "initialize": self._handle_initialize,
            "initialized": self._handle_initialized,
            "shutdown": self._handle_shutdown,
            "exit": self._handle_exit,
            "textDocument/didOpen": self._handle_did_open,
            "textDocument/didChange": self._handle_did_change,
            "textDocument/didSave": self._handle_did_save,
            "textDocument/didClose": self._handle_did_close,
            "textDocument/hover": self._handle_hover,
            "textDocument/codeAction": self._handle_code_action,
            "workspace/didChangeConfiguration": self._handle_config_change,
            "complianceAgent/analyzeDocument": self._handle_analyze_document,
            "complianceAgent/setRegulations": self._handle_set_regulations,
            "complianceAgent/addCustomPattern": self._handle_add_custom_pattern,
        }

    async def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """Handle an incoming LSP message."""
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")

        if method in self._handlers:
            try:
                result = await self._handlers[method](params)
                if msg_id is not None:
                    return self._create_response(msg_id, result)
            except Exception as e:
                logger.exception(f"Error handling {method}: {e}")
                if msg_id is not None:
                    return self._create_error_response(msg_id, -32603, str(e))
        else:
            logger.warning(f"Unknown method: {method}")
            if msg_id is not None:
                return self._create_error_response(msg_id, -32601, f"Method not found: {method}")

        return None

    def _create_response(self, msg_id: int | str, result: Any) -> dict[str, Any]:
        """Create a successful LSP response."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result,
        }

    def _create_error_response(
        self,
        msg_id: int | str,
        code: int,
        message: str,
    ) -> dict[str, Any]:
        """Create an LSP error response."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": code,
                "message": message,
            },
        }

    def _create_notification(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Create an LSP notification (no id = no response expected)."""
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

    async def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle initialize request."""
        self._initialized = True

        return {
            "capabilities": {
                "textDocumentSync": {
                    "openClose": True,
                    "change": 1,  # Full sync
                    "save": {"includeText": True},
                },
                "hoverProvider": True,
                "codeActionProvider": {
                    "codeActionKinds": ["quickfix", "source"],
                },
                "diagnosticProvider": {
                    "interFileDependencies": False,
                    "workspaceDiagnostics": False,
                },
                "executeCommandProvider": {
                    "commands": [
                        "complianceAgent.openDocumentation",
                        "complianceAgent.applyFix",
                        "complianceAgent.ignoreIssue",
                    ],
                },
            },
            "serverInfo": {
                "name": "ComplianceAgent LSP",
                "version": "0.1.0",
            },
        }

    async def _handle_initialized(self, params: dict[str, Any]) -> None:
        """Handle initialized notification."""
        logger.info("ComplianceAgent LSP server initialized")

    async def _handle_shutdown(self, params: dict[str, Any]) -> None:
        """Handle shutdown request."""
        self._shutdown_requested = True
        # Cancel any pending debounce tasks
        for task in self._debounce_tasks.values():
            task.cancel()
        self._debounce_tasks.clear()

    async def _handle_exit(self, params: dict[str, Any]) -> None:
        """Handle exit notification."""
        # Server process should exit

    async def _handle_did_open(self, params: dict[str, Any]) -> dict[str, Any] | None:
        """Handle textDocument/didOpen notification."""
        text_document = params.get("textDocument", {})
        uri = text_document.get("uri", "")
        language_id = text_document.get("languageId", "")
        version = text_document.get("version", 0)
        text = text_document.get("text", "")

        self.documents[uri] = TextDocumentItem(
            uri=uri,
            language_id=language_id,
            version=version,
            text=text,
        )

        if self.config.analyze_on_open:
            return await self._publish_diagnostics(uri)
        return None

    async def _handle_did_change(self, params: dict[str, Any]) -> dict[str, Any] | None:
        """Handle textDocument/didChange notification."""
        text_document = params.get("textDocument", {})
        uri = text_document.get("uri", "")
        version = text_document.get("version", 0)
        changes = params.get("contentChanges", [])

        if uri in self.documents and changes:
            # For full sync, use the last change
            self.documents[uri].text = changes[-1].get("text", "")
            self.documents[uri].version = version

            if self.config.analyze_on_change:
                # Debounce analysis to avoid overwhelming the analyzer
                return await self._debounced_analyze(uri)
        return None

    async def _handle_did_save(self, params: dict[str, Any]) -> dict[str, Any] | None:
        """Handle textDocument/didSave notification."""
        text_document = params.get("textDocument", {})
        uri = text_document.get("uri", "")
        text = params.get("text")

        if uri in self.documents:
            if text is not None:
                self.documents[uri].text = text

            if self.config.analyze_on_save:
                # Cancel any pending debounced analysis
                if uri in self._debounce_tasks:
                    self._debounce_tasks[uri].cancel()
                return await self._publish_diagnostics(uri)
        return None

    async def _handle_did_close(self, params: dict[str, Any]) -> dict[str, Any] | None:
        """Handle textDocument/didClose notification."""
        text_document = params.get("textDocument", {})
        uri = text_document.get("uri", "")

        if uri in self.documents:
            del self.documents[uri]

        if uri in self._debounce_tasks:
            self._debounce_tasks[uri].cancel()
            del self._debounce_tasks[uri]

        # Clear diagnostics for closed document
        return self._create_notification(
            "textDocument/publishDiagnostics",
            {"uri": uri, "diagnostics": []},
        )

    async def _handle_hover(self, params: dict[str, Any]) -> dict[str, Any] | None:
        """Handle textDocument/hover request."""
        text_document = params.get("textDocument", {})
        uri = text_document.get("uri", "")
        position = params.get("position", {})
        line = position.get("line", 0)
        character = position.get("character", 0)

        if uri not in self.documents:
            return None

        doc = self.documents[uri]
        return self.analyzer.get_hover_info(uri, doc.text, line, character)

    async def _handle_code_action(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Handle textDocument/codeAction request."""
        text_document = params.get("textDocument", {})
        uri = text_document.get("uri", "")
        context = params.get("context", {})
        diagnostics = context.get("diagnostics", [])

        actions = []
        for diag in diagnostics:
            if diag.get("source") == "ComplianceAgent":
                data = diag.get("data", {})
                code = diag.get("code", "")

                # Add quick fix actions based on diagnostic
                actions.append({
                    "title": f"Fix: {diag.get('message', '')[:50]}...",
                    "kind": "quickfix",
                    "diagnostics": [diag],
                    "command": {
                        "title": "Apply Fix",
                        "command": "complianceAgent.applyFix",
                        "arguments": [uri, code, data],
                    },
                })

                # Add ignore action
                actions.append({
                    "title": f"Ignore {code} for this line",
                    "kind": "quickfix",
                    "diagnostics": [diag],
                    "command": {
                        "title": "Ignore Issue",
                        "command": "complianceAgent.ignoreIssue",
                        "arguments": [uri, code, diag.get("range")],
                    },
                })

                # Add documentation link
                if data.get("regulation"):
                    actions.append({
                        "title": f"View {data['regulation']} documentation",
                        "kind": "source",
                        "command": {
                            "title": "Open Documentation",
                            "command": "complianceAgent.openDocumentation",
                            "arguments": [data["regulation"], data.get("article_reference")],
                        },
                    })

        return actions

    async def _handle_config_change(self, params: dict[str, Any]) -> None:
        """Handle workspace/didChangeConfiguration notification."""
        settings = params.get("settings", {}).get("complianceAgent", {})

        if "enabledRegulations" in settings:
            self.config.enabled_regulations = settings["enabledRegulations"]
            self.analyzer = IDEComplianceAnalyzer(
                enabled_regulations=self.config.enabled_regulations,
                severity_threshold=self.config.severity_threshold,
            )

        if "severityThreshold" in settings:
            threshold = settings["severityThreshold"]
            self.config.severity_threshold = DiagnosticSeverity(threshold)
            self.analyzer.severity_threshold = self.config.severity_threshold

        # Re-analyze all open documents with new config
        for uri in self.documents:
            await self._publish_diagnostics(uri)

    async def _handle_analyze_document(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle custom complianceAgent/analyzeDocument request."""
        uri = params.get("uri", "")

        if uri in self.documents:
            doc = self.documents[uri]
            result = self.analyzer.analyze_document(
                uri=uri,
                content=doc.text,
                language=doc.language_id,
                version=doc.version,
            )
            return {
                "uri": result.uri,
                "version": result.version,
                "diagnosticsCount": len(result.diagnostics),
                "analysisTimeMs": result.analysis_time_ms,
                "patternsChecked": result.patterns_checked,
            }

        return {"error": "Document not found"}

    async def _handle_set_regulations(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle custom complianceAgent/setRegulations request."""
        regulations = params.get("regulations", [])
        self.config.enabled_regulations = regulations
        self.analyzer = IDEComplianceAnalyzer(
            enabled_regulations=regulations,
            severity_threshold=self.config.severity_threshold,
        )
        return {"success": True, "enabledRegulations": regulations}

    async def _handle_add_custom_pattern(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle custom complianceAgent/addCustomPattern request."""
        name = params.get("name", "")
        pattern = params.get("pattern", "")
        message = params.get("message", "")
        severity = params.get("severity", "warning")
        regulation = params.get("regulation")

        if not all([name, pattern, message]):
            return {"success": False, "error": "Missing required fields"}

        self.analyzer.add_custom_pattern(
            name=name,
            pattern=pattern,
            message=message,
            severity=DiagnosticSeverity(severity),
            regulation=regulation,
        )
        return {"success": True, "patternName": name}

    async def _debounced_analyze(self, uri: str) -> None:
        """Debounce document analysis to reduce CPU usage during typing."""
        # Cancel existing debounce task for this URI
        if uri in self._debounce_tasks:
            self._debounce_tasks[uri].cancel()

        async def delayed_analyze():
            await asyncio.sleep(self.config.debounce_ms / 1000)
            await self._publish_diagnostics(uri)

        self._debounce_tasks[uri] = asyncio.create_task(delayed_analyze())

    async def _publish_diagnostics(self, uri: str) -> dict[str, Any]:
        """Analyze document and publish diagnostics."""
        if uri not in self.documents:
            return self._create_notification(
                "textDocument/publishDiagnostics",
                {"uri": uri, "diagnostics": []},
            )

        doc = self.documents[uri]
        result = self.analyzer.analyze_document(
            uri=uri,
            content=doc.text,
            language=doc.language_id,
            version=doc.version,
        )

        lsp_diagnostics = [d.to_lsp_diagnostic() for d in result.diagnostics]

        return self._create_notification(
            "textDocument/publishDiagnostics",
            {
                "uri": uri,
                "version": doc.version,
                "diagnostics": lsp_diagnostics,
            },
        )

    async def run_stdio(self) -> None:
        """Run the LSP server over stdio (for production use)."""
        import sys

        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())

        while not self._shutdown_requested:
            try:
                # Read Content-Length header
                header = await reader.readline()
                if not header:
                    break

                content_length = 0
                while header and header.strip():
                    if header.startswith(b"Content-Length:"):
                        content_length = int(header.split(b":")[1].strip())
                    header = await reader.readline()

                if content_length == 0:
                    continue

                # Read message body
                body = await reader.read(content_length)
                message = json.loads(body.decode("utf-8"))

                # Handle message
                response = await self.handle_message(message)

                # Send response if any
                if response:
                    response_body = json.dumps(response).encode("utf-8")
                    response_header = f"Content-Length: {len(response_body)}\r\n\r\n"
                    writer.write(response_header.encode("utf-8"))
                    writer.write(response_body)
                    await writer.drain()

            except Exception as e:
                logger.exception(f"LSP server error: {e}")
                break

        writer.close()
