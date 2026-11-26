from app.core.classifier import classify_task

def test_simple_task_uses_flash_tier():
    assert classify_task('customer_support', [{'role': 'user', 'content': 'Olá'}]) == 'flash'

def test_explicit_analysis_uses_advanced_tier():
    assert classify_task('analysis', [{'role': 'user', 'content': 'Resume isto'}]) == 'advanced'
