"""Metrics calculation utilities for marketing analysis."""
from app.data.mock_users import AVG_ORDER_VALUE


class MetricsCalculator:
    """Calculate marketing KPIs and metrics."""

    def __init__(self, avg_order_value: float = AVG_ORDER_VALUE):
        """Initialize calculator.

        Args:
            avg_order_value: Average order value in CNY.
        """
        self.avg_order_value = avg_order_value

    def calculate_conversion_rate(
        self,
        audience_size: int,
        base_rate: float = 0.05
    ) -> float:
        """Estimate conversion rate based on audience size and quality.

        Args:
            audience_size: Size of the selected audience.
            base_rate: Base conversion rate (0-1). Defaults to 5%.

        Returns:
            Estimated conversion rate (0-1).
        """
        # Simulate: smaller, more targeted audiences have higher conversion
        if audience_size < 100:
            return min(base_rate * 1.8, 0.15)
        elif audience_size < 300:
            return min(base_rate * 1.5, 0.12)
        elif audience_size < 500:
            return min(base_rate * 1.2, 0.10)
        else:
            return base_rate

    def calculate_estimated_revenue(
        self,
        audience_size: int,
        conversion_rate: float,
        avg_order_value: float | None = None
    ) -> float:
        """Calculate estimated revenue from marketing campaign.

        Args:
            audience_size: Size of the selected audience.
            conversion_rate: Estimated conversion rate (0-1).
            avg_order_value: Average order value. If None, uses self.avg_order_value.

        Returns:
            Estimated revenue in CNY.
        """
        aov = avg_order_value or self.avg_order_value
        return audience_size * conversion_rate * aov

    def calculate_roi(
        self,
        estimated_revenue: float,
        campaign_cost: float = 10000  # 默认活动成本
    ) -> float:
        """Calculate estimated ROI.

        Args:
            estimated_revenue: Estimated revenue from campaign.
            campaign_cost: Campaign cost in CNY. Defaults to 10,000.

        Returns:
            ROI as a percentage (0-100+).
        """
        if campaign_cost <= 0:
            return 0
        return (estimated_revenue - campaign_cost) / campaign_cost * 100

    def calculate_reach_rate(
        self,
        audience_size: int,
        total_users: int = 1000
    ) -> float:
        """Calculate reach rate as percentage of total users.

        Args:
            audience_size: Size of the selected audience.
            total_users: Total user base. Defaults to 1000.

        Returns:
            Reach rate as a percentage (0-100).
        """
        if total_users <= 0:
            return 0
        return (audience_size / total_users) * 100

    def calculate_audience_quality_score(
        self,
        avg_user_score: float,
        audience_tier_distribution: dict[str, int]
    ) -> float:
        """Calculate audience quality score.

        Args:
            avg_user_score: Average matching score of selected users (0-100).
            audience_tier_distribution: Distribution of tiers, e.g., {'VVIP': 10, 'VIP': 20, 'Member': 15}

        Returns:
            Quality score (0-100).
        """
        # Base score from user matching
        quality = avg_user_score * 0.5

        # Bonus for high-tier distribution
        tier_weights = {'VVIP': 0.8, 'VIP': 0.5, 'Member': 0.2}
        total_users = sum(audience_tier_distribution.values())

        if total_users > 0:
            tier_score = 0
            for tier, count in audience_tier_distribution.items():
                weight = tier_weights.get(tier, 0)
                tier_score += (count / total_users) * weight * 50
            quality += tier_score

        return min(100, quality)

    def estimate_metrics(
        self,
        audience_size: int,
        avg_user_score: float,
        audience_tier_distribution: dict[str, int],
        campaign_cost: float = 10000
    ) -> dict:
        """Estimate all key metrics for a campaign.

        Args:
            audience_size: Size of selected audience.
            avg_user_score: Average user match score.
            audience_tier_distribution: Tier distribution of audience.
            campaign_cost: Campaign cost in CNY.

        Returns:
            Dictionary containing all metrics.
        """
        conversion_rate = self.calculate_conversion_rate(audience_size)
        estimated_revenue = self.calculate_estimated_revenue(audience_size, conversion_rate)
        roi = self.calculate_roi(estimated_revenue, campaign_cost)
        reach_rate = self.calculate_reach_rate(audience_size)
        quality_score = self.calculate_audience_quality_score(avg_user_score, audience_tier_distribution)

        return {
            "audience_size": audience_size,
            "conversion_rate": conversion_rate,
            "estimated_revenue": estimated_revenue,
            "roi": roi,
            "reach_rate": reach_rate,
            "quality_score": quality_score,
            "campaign_cost": campaign_cost,
            "avg_user_score": avg_user_score
        }


# Global calculator instance
_calculator: MetricsCalculator | None = None


def get_calculator() -> MetricsCalculator:
    """Get or create global metrics calculator."""
    global _calculator
    if _calculator is None:
        _calculator = MetricsCalculator()
    return _calculator
