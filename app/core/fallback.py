from dataclasses import dataclass

@dataclass(frozen=True)
class FallbackPolicy:
    enabled: bool
    provider_order: tuple[str, ...]

    @classmethod
    def from_settings(cls, settings):
        return cls(enabled=settings.enable_fallback, provider_order=tuple(settings.fallback_order))

    def candidates(self, preferred: str, available: list[str]) -> list[str]:
        if not self.enabled:
            return [preferred] if preferred in available else []
        order = [preferred, *self.provider_order, 'gemini', 'openai', 'anthropic']
        return list(dict.fromkeys(name for name in order if name in available))
