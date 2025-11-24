from rest_framework.throttling import SimpleRateThrottle

class DaasIngestRateThrottle(SimpleRateThrottle):
    scope = "daas"
    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": request.META.get("REMOTE_ADDR")
        }
