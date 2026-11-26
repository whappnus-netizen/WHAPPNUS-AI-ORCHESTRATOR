from dataclasses import dataclass

@dataclass(frozen=True)
class TenantContext:
    organization_id: str
    request_id: str
    # organization_id is trusted only behind the authenticated WHAPPNUS server boundary.
