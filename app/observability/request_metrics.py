from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUESTS = Counter("whappnus_orchestrator_requests_total", "Orchestrator requests", ["provider", "outcome"])
LATENCY = Histogram("whappnus_orchestrator_request_duration_seconds", "Provider request duration", ["provider"])
FALLBACKS = Counter("whappnus_orchestrator_fallbacks_total", "Provider fallbacks")
ERRORS = Counter("whappnus_orchestrator_provider_errors_total", "Provider errors", ["provider", "code"])

def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
