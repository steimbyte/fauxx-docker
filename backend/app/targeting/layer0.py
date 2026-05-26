from app.models.enums import CategoryPool


class UniformEntropyLayer:
    """
    Layer 0: Uniform Entropy Baseline
    Always active - equal probability across all categories.
    """

    @staticmethod
    def get_weights() -> dict[CategoryPool, float]:
        """Returns uniform weights (1.0 for all categories)."""
        return {cat: 1.0 for cat in CategoryPool}
