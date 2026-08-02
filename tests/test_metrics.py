import math

from tennisbet.evaluation.metrics import (
    accuracy, brier_score, calibration_bins, evaluate,
    expected_calibration_error, log_loss,
)


def test_perfect_predictions():
    y = [1, 0, 1, 0]
    p = [0.999999, 0.000001, 0.999999, 0.000001]
    assert log_loss(y, p) < 1e-5
    assert brier_score(y, p) < 1e-5
    assert accuracy(y, p) == 1.0


def test_coinflip_logloss_is_ln2():
    y = [1, 0, 1, 0]
    assert math.isclose(log_loss(y, [0.5] * 4), math.log(2), rel_tol=1e-9)


def test_confident_and_wrong_is_punished():
    assert log_loss([1], [0.01]) > log_loss([1], [0.5])


def test_accuracy_ignores_calibration():
    """Two models, same accuracy, very different log loss — why accuracy misleads."""
    y = [1, 1, 0, 0]
    timid = [0.51, 0.51, 0.49, 0.49]
    bold = [0.99, 0.99, 0.01, 0.01]
    assert accuracy(y, timid) == accuracy(y, bold) == 1.0
    assert log_loss(y, bold) < log_loss(y, timid)


def test_calibration_error_zero_when_calibrated():
    # 100 samples at p=0.7 with exactly 70 positives
    y = [1] * 70 + [0] * 30
    p = [0.7] * 100
    assert expected_calibration_error(y, p) < 1e-9


def test_calibration_error_detects_bias():
    y = [1] * 50 + [0] * 50
    p = [0.9] * 100  # says 90%, truth is 50%
    assert expected_calibration_error(y, p) > 0.3


def test_calibration_bins_cover_all():
    y = [1, 0, 1, 0]
    p = [0.1, 0.4, 0.6, 0.95]
    bins = calibration_bins(y, p, n_bins=10)
    assert sum(b["n"] for b in bins) == 4


def test_evaluate_keys():
    m = evaluate([1, 0], [0.6, 0.4])
    assert {"n", "log_loss", "brier", "ece", "accuracy", "base_rate"} <= set(m)
