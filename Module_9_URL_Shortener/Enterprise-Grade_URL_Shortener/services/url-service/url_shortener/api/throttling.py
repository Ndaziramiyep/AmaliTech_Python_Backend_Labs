from rest_framework.throttling import UserRateThrottle

TIER_RATES = {
    "Premium": "1000/day",
    "Admin": "1000/day",
    "Free": "100/day",
}


class TieredUserRateThrottle(UserRateThrottle):
    """Limits write requests per user, at a daily rate that scales with their subscription tier."""

    scope = "tiered_user"

    def allow_request(self, request, view):
        """Picks the rate matching the caller's tier before running DRF's standard throttle check."""
        tier = getattr(request.user, "tier", "Free") if request.user.is_authenticated else "Free"
        self.rate = TIER_RATES.get(tier, TIER_RATES["Free"])
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)
