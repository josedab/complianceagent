"""Prometheus metrics for ComplianceAgent."""

import time
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class MetricsCollector:
    """Collects and exposes Prometheus metrics."""

    def __init__(self):
        self._request_count: dict[str, int] = {}
        self._request_latency: dict[str, list[float]] = {}
        self._error_count: dict[str, int] = {}
        self._active_requests: int = 0

        # Compliance-specific metrics
        self._regulations_processed: int = 0
        self._requirements_extracted: int = 0
        self._repositories_analyzed: int = 0
        self._code_generated: int = 0
        self._copilot_requests: int = 0
        self._copilot_errors: int = 0
        self._copilot_latency: list[float] = []

    def inc_request(self, method: str, path: str, status: int) -> None:
        """Increment request counter."""
        key = f"{method}:{path}:{status}"
        self._request_count[key] = self._request_count.get(key, 0) + 1

    def observe_latency(self, method: str, path: str, latency: float) -> None:
        """Record request latency."""
        key = f"{method}:{path}"
        if key not in self._request_latency:
            self._request_latency[key] = []
        self._request_latency[key].append(latency)
        # Keep only last 1000 observations to prevent memory growth
        if len(self._request_latency[key]) > 1000:
            self._request_latency[key] = self._request_latency[key][-1000:]

    def inc_error(self, error_type: str) -> None:
        """Increment error counter."""
        self._error_count[error_type] = self._error_count.get(error_type, 0) + 1

    def inc_active_requests(self) -> None:
        """Increment active requests gauge."""
        self._active_requests += 1

    def dec_active_requests(self) -> None:
        """Decrement active requests gauge."""
        self._active_requests = max(0, self._active_requests - 1)

    # Compliance-specific metric methods
    def inc_regulations_processed(self) -> None:
        self._regulations_processed += 1

    def inc_requirements_extracted(self, count: int = 1) -> None:
        self._requirements_extracted += count

    def inc_repositories_analyzed(self) -> None:
        self._repositories_analyzed += 1

    def inc_code_generated(self) -> None:
        self._code_generated += 1

    def inc_copilot_request(self) -> None:
        self._copilot_requests += 1

    def inc_copilot_error(self) -> None:
        self._copilot_errors += 1

    def observe_copilot_latency(self, latency: float) -> None:
        self._copilot_latency.append(latency)
        if len(self._copilot_latency) > 1000:
            self._copilot_latency = self._copilot_latency[-1000:]

    def _calculate_percentile(self, values: list[float], percentile: float) -> float:
        """Calculate percentile from a list of values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []

        # Request metrics
        lines.append("# HELP http_requests_total Total HTTP requests")
        lines.append("# TYPE http_requests_total counter")
        for key, count in self._request_count.items():
            method, path, status = key.split(":")
            lines.append(
                f'http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
            )

        # Active requests
        lines.append("# HELP http_requests_active Current active HTTP requests")
        lines.append("# TYPE http_requests_active gauge")
        lines.append(f"http_requests_active {self._active_requests}")

        # Latency metrics
        lines.append("# HELP http_request_duration_seconds HTTP request latency")
        lines.append("# TYPE http_request_duration_seconds summary")
        for key, latencies in self._request_latency.items():
            if latencies:
                method, path = key.split(":")
                p50 = self._calculate_percentile(latencies, 50)
                p95 = self._calculate_percentile(latencies, 95)
                p99 = self._calculate_percentile(latencies, 99)
                avg = sum(latencies) / len(latencies)
                lines.append(
                    f'http_request_duration_seconds{{method="{method}",path="{path}",quantile="0.5"}} {p50:.6f}'
                )
                lines.append(
                    f'http_request_duration_seconds{{method="{method}",path="{path}",quantile="0.95"}} {p95:.6f}'
                )
                lines.append(
                    f'http_request_duration_seconds{{method="{method}",path="{path}",quantile="0.99"}} {p99:.6f}'
                )
                lines.append(
                    f'http_request_duration_seconds_sum{{method="{method}",path="{path}"}} {sum(latencies):.6f}'
                )
                lines.append(
                    f'http_request_duration_seconds_count{{method="{method}",path="{path}"}} {len(latencies)}'
                )

        # Error metrics
        lines.append("# HELP errors_total Total errors by type")
        lines.append("# TYPE errors_total counter")
        for error_type, count in self._error_count.items():
            lines.append(f'errors_total{{type="{error_type}"}} {count}')

        # Compliance metrics
        lines.append("# HELP complianceagent_regulations_processed_total Total regulations processed")
        lines.append("# TYPE complianceagent_regulations_processed_total counter")
        lines.append(f"complianceagent_regulations_processed_total {self._regulations_processed}")

        lines.append("# HELP complianceagent_requirements_extracted_total Total requirements extracted")
        lines.append("# TYPE complianceagent_requirements_extracted_total counter")
        lines.append(f"complianceagent_requirements_extracted_total {self._requirements_extracted}")

        lines.append("# HELP complianceagent_repositories_analyzed_total Total repositories analyzed")
        lines.append("# TYPE complianceagent_repositories_analyzed_total counter")
        lines.append(f"complianceagent_repositories_analyzed_total {self._repositories_analyzed}")

        lines.append("# HELP complianceagent_code_generated_total Total code generations")
        lines.append("# TYPE complianceagent_code_generated_total counter")
        lines.append(f"complianceagent_code_generated_total {self._code_generated}")

        # Copilot metrics
        lines.append("# HELP complianceagent_copilot_requests_total Total Copilot API requests")
        lines.append("# TYPE complianceagent_copilot_requests_total counter")
        lines.append(f"complianceagent_copilot_requests_total {self._copilot_requests}")

        lines.append("# HELP complianceagent_copilot_errors_total Total Copilot API errors")
        lines.append("# TYPE complianceagent_copilot_errors_total counter")
        lines.append(f"complianceagent_copilot_errors_total {self._copilot_errors}")

        if self._copilot_latency:
            lines.append("# HELP complianceagent_copilot_duration_seconds Copilot API latency")
            lines.append("# TYPE complianceagent_copilot_duration_seconds summary")
            p50 = self._calculate_percentile(self._copilot_latency, 50)
            p95 = self._calculate_percentile(self._copilot_latency, 95)
            p99 = self._calculate_percentile(self._copilot_latency, 99)
            lines.append(f'complianceagent_copilot_duration_seconds{{quantile="0.5"}} {p50:.6f}')
            lines.append(f'complianceagent_copilot_duration_seconds{{quantile="0.95"}} {p95:.6f}')
            lines.append(f'complianceagent_copilot_duration_seconds{{quantile="0.99"}} {p99:.6f}')
            lines.append(f"complianceagent_copilot_duration_seconds_sum {sum(self._copilot_latency):.6f}")
            lines.append(f"complianceagent_copilot_duration_seconds_count {len(self._copilot_latency)}")

        return "\n".join(lines) + "\n"


# Global metrics collector instance
metrics = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics endpoint itself to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Normalize path to avoid high cardinality
        path = self._normalize_path(request.url.path)
        method = request.method

        metrics.inc_active_requests()
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            latency = time.perf_counter() - start_time

            metrics.inc_request(method, path, response.status_code)
            metrics.observe_latency(method, path, latency)

            return response
        except Exception as e:
            latency = time.perf_counter() - start_time
            metrics.inc_request(method, path, 500)
            metrics.observe_latency(method, path, latency)
            metrics.inc_error(type(e).__name__)
            raise
        finally:
            metrics.dec_active_requests()

    def _normalize_path(self, path: str) -> str:
        """Normalize path to reduce cardinality (replace UUIDs and IDs)."""
        import re

        # Replace UUIDs
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            path,
            flags=re.IGNORECASE,
        )
        # Replace numeric IDs
        path = re.sub(r"/\d+(/|$)", "/{id}\\1", path)
        return path


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector."""
    return metrics
