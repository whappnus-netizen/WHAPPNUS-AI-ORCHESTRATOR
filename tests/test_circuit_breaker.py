from app.core.circuit_breaker import CircuitBreaker

def test_circuit_breaker_opens_after_threshold_and_resets_on_success():
    breaker = CircuitBreaker(failure_threshold=2, reset_seconds=30)
    breaker.record_failure()
    assert not breaker.is_open
    breaker.record_failure()
    assert breaker.is_open
    breaker.record_success()
    assert not breaker.is_open
