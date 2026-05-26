from app.models.enums import CategoryPool

MIN_WEIGHT = 0.001


class WeightNormalizer:
    """Normalizes category weights so they sum to 1.0"""

    @staticmethod
    def normalize(weights: dict[CategoryPool, float]) -> dict[CategoryPool, float]:
        """
        Normalize weights to sum = 1.0, clamping minimum to MIN_WEIGHT.
        Two-pass algorithm to handle clamping while preserving sum.
        """
        if not weights:
            return {c: 1.0 / len(CategoryPool) for c in CategoryPool}

        # First pass: clamp to minimum
        clamped = {k: max(v, MIN_WEIGHT) for k, v in weights.items()}
        
        # Add missing categories with minimum weight
        for cat in CategoryPool:
            if cat not in clamped:
                clamped[cat] = MIN_WEIGHT

        # Calculate sum
        total = sum(clamped.values())
        
        # Second pass: normalize and ensure minimum
        result = {}
        remainder = 1.0
        count = len(clamped)
        
        for cat, weight in clamped.items():
            if count == 1:
                result[cat] = remainder
            else:
                normalized = (weight / total) * remainder
                if normalized < MIN_WEIGHT:
                    result[cat] = MIN_WEIGHT
                    remainder -= MIN_WEIGHT
                else:
                    result[cat] = normalized
            count -= 1

        return result

    @staticmethod
    def normalize_complete(weights: dict[CategoryPool, float]) -> dict[CategoryPool, float]:
        """Fill missing categories with MIN_WEIGHT, then normalize."""
        complete = dict(weights)
        for cat in CategoryPool:
            if cat not in complete:
                complete[cat] = MIN_WEIGHT
        return WeightNormalizer.normalize(complete)
