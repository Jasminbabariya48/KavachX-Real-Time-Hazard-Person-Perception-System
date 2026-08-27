"""Alert Severity and Debounce Policy."""
SEVERITY_POLICY = {
    "fire": "CRITICAL",
    "smoke": "WARNING",
    "person": "WARNING"
}

EVENT_TYPE_MAP = {
    "fire": "HAZARD_DETECTED",
    "smoke": "HAZARD_DETECTED",
    "person": "PERSON_DETECTED"
}
