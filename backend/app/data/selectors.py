"""User filtering and selection logic."""
from typing import Any
from app.data.mock_users import User, MOCK_USERS, AVG_ORDER_VALUE, MIN_TIER_RANK


class AudienceSelector:
    """Select audience based on marketing criteria."""

    def __init__(self, users: list[User] | None = None):
        """Initialize selector with user pool."""
        self.users = users or MOCK_USERS.copy()

    def filter_by_tier(self, tiers: list[str] | None = None) -> list[User]:
        """Filter users by membership tier.

        Args:
            tiers: List of membership tiers to include. If None, returns all users.
                  Valid values: 'VVIP', 'VIP', 'Member'

        Returns:
            Filtered list of users.
        """
        if not tiers:
            return self.users.copy()
        return [u for u in self.users if u["tier"] in tiers]

    def filter_by_min_score(self, min_score: int) -> list[User]:
        """Filter users with score >= min_score.

        Args:
            min_score: Minimum score threshold.

        Returns:
            Filtered list of users.
        """
        return [u for u in self.users if u["score"] >= min_score]

    def filter_by_behavior(self, behavior_criteria: dict[str, Any]) -> list[User]:
        """Filter users by behavior criteria.

        Args:
            behavior_criteria: Dictionary with behavior conditions.
                              Supported keys:
                              - 'browse_frequency': Minimum page views (simulated in score)
                              - 'purchase_history': Whether user has purchase history
                              - 'engagement_level': 'high', 'medium', 'low'

        Returns:
            Filtered list of users.
        """
        filtered = self.users.copy()

        if "browse_frequency" in behavior_criteria:
            min_frequency = behavior_criteria["browse_frequency"]
            # Simulate: higher score indicates more browsing
            filtered = [u for u in filtered if u["score"] >= min_frequency]

        if "engagement_level" in behavior_criteria:
            level = behavior_criteria["engagement_level"]
            if level == "high":
                filtered = [u for u in filtered if u["score"] >= 90]
            elif level == "medium":
                filtered = [u for u in filtered if 80 <= u["score"] < 90]
            elif level == "low":
                filtered = [u for u in filtered if u["score"] < 80]

        return filtered

    def calculate_match_score(
        self,
        user: User,
        tier_weights: dict[str, float] | None = None,
        score_weight: float = 0.3,
        behavior_weight: float = 0.7
    ) -> float:
        """Calculate user's match score against criteria.

        Args:
            user: User to evaluate.
            tier_weights: Weight for each tier. Default: {'VVIP': 1.0, 'VIP': 0.8, 'Member': 0.5}
            score_weight: Weight of user's base score.
            behavior_weight: Weight of behavior indicators.

        Returns:
            Match score between 0-100.
        """
        if tier_weights is None:
            tier_weights = {'VVIP': 1.0, 'VIP': 0.8, 'Member': 0.5}

        tier_score = tier_weights.get(user["tier"], 0.5) * 50  # Normalize to 50
        base_score = user["score"] * (score_weight / 100)
        behavior_score = 0

        # Simulate behavior scoring: mentioned in reason field
        if "购买" in user["reason"]:
            behavior_score += 20
        if "浏览" in user["reason"]:
            behavior_score += 15
        if "加购" in user["reason"]:
            behavior_score += 15
        if "参加" in user["reason"]:
            behavior_score += 10

        behavior_score *= (behavior_weight / 100)

        total_score = tier_score + base_score + behavior_score
        return min(100, total_score)  # Cap at 100

    def rank_users(
        self,
        users: list[User] | None = None,
        limit: int = 50,
        recalculate_score: bool = False
    ) -> list[dict]:
        """Rank users and return top N.

        Args:
            users: Users to rank. If None, uses self.users.
            limit: Number of top users to return.
            recalculate_score: If True, recalculate match scores. Otherwise use original score.

        Returns:
            List of users with match scores, sorted by score descending.
        """
        users_to_rank = users or self.users

        if recalculate_score:
            ranked = [
                {**u, "matchScore": self.calculate_match_score(u)}
                for u in users_to_rank
            ]
        else:
            ranked = [
                {**u, "matchScore": float(u["score"])}
                for u in users_to_rank
            ]

        # Sort by matchScore descending
        ranked.sort(key=lambda x: x["matchScore"], reverse=True)

        return ranked[:limit]

    def select_for_campaign(
        self,
        intent: dict[str, Any],
        apply_recalculation: bool = True
    ) -> tuple[list[dict], dict[str, Any]]:
        """Select audience for marketing campaign based on intent.

        Args:
            intent: Parsed user intent containing:
                   - 'kpi': Primary KPI (e.g., 'conversion_rate', 'revenue')
                   - 'target_tiers': List of membership tiers
                   - 'behavior_filters': Behavior-based criteria
                   - 'size_preference': Preferred audience size range
            apply_recalculation: Whether to recalculate match scores based on intent.

        Returns:
            Tuple of (selected_users, metadata)
        """
        # Step 1: Filter by tier
        tiers = intent.get("target_tiers", ["VVIP", "VIP", "Member"])
        filtered = self.filter_by_tier(tiers)

        # Step 2: Apply behavior filters if any
        behavior_filters = intent.get("behavior_filters", {})
        if behavior_filters:
            filtered = self.filter_by_behavior(behavior_filters)

        # Step 3: Rank and select
        size_preference = intent.get("size_preference", {"min": 50, "max": 500})
        limit = size_preference.get("max", len(filtered))

        selected = self.rank_users(filtered, limit=limit, recalculate_score=apply_recalculation)

        # Step 4: Build metadata
        metadata = {
            "total_candidates": len(self.users),
            "after_filter": len(filtered),
            "final_selected": len(selected),
            "top_tiers": [u["tier"] for u in selected[:5]],
            "avg_score": sum(u["matchScore"] for u in selected) / len(selected) if selected else 0
        }

        return selected, metadata


def select_audience(
    intent: dict[str, Any],
    users: list[User] | None = None
) -> tuple[list[dict], dict[str, Any]]:
    """Convenience function to select audience.

    Args:
        intent: Marketing intent/criteria.
        users: Optional user pool. If None, uses MOCK_USERS.

    Returns:
        Tuple of (selected_users, metadata)
    """
    selector = AudienceSelector(users)
    return selector.select_for_campaign(intent)
