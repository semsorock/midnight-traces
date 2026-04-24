import pytest
from pipeline import validate_date

def test_validate_date():
    assert validate_date("2025-12-05") is True
    assert validate_date("2025-13-05") is False
    assert validate_date("invalid") is False
