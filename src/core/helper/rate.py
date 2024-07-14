from src.core.app_enum import PredictionRate

prediction_to_violation_rate = {
    0: PredictionRate.LOW,
    1: PredictionRate.MEDIUM,
    2: PredictionRate.HIGH,
}


def prediction_to_violation(prediction: int | None) -> PredictionRate:
    return prediction_to_violation_rate.get(prediction, PredictionRate.UNDETERMINED)
