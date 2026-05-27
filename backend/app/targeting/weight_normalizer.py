from app.models.enums import CategoryPool

MIN_WEIGHT = 0.001


class WeightNormalizer:
    """Normalizes category weights so they sum to 1.0"""

    @staticmethod
    def normalize(weights: dict[CategoryPool, float]) -> dict[CategoryPool, float]:
        """
        Normalize weights to sum = 1.0.
        """
        if not weights:
            return {c: 1.0 / len(CategoryPool) for c in CategoryPool}

        # Ensure all categories exist
        complete = dict(weights)
        for cat in CategoryPool:
            if cat not in complete:
                complete[cat] = MIN_WEIGHT

        # Calculate sum
        total = sum(complete.values())
        
        if total == 0:
            return {c: 1.0 / len(CategoryPool) for c in CategoryPool}
        
        # Normalize to sum = 1.0
        return {cat: max(MIN_WEIGHT, weight / total) for cat, weight in complete.items()}

    @staticmethod
    def normalize_complete(weights: dict[CategoryPool, float]) -> dict[CategoryPool, float]:
        """Fill missing categories with MIN_WEIGHT, then normalize."""
        return WeightNormalizer.normalize(weights)
