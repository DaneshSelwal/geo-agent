import pytest

from app.models.analysis import AnalysisResult, DataQuality, Methodology
from app.validation.validator import (
    _get_quality_level,
    validate_analysis_result,
)


def make_ndvi_result(
    source_images=100,
    usable_images=50,
    coverage=1.0,
    mean_ndvi=0.5,
):
    return AnalysisResult(
        analysis_type="ndvi_analysis",
        findings={
            "mean_ndvi": mean_ndvi,
            "minimum_ndvi": 0.1,
            "maximum_ndvi": 0.8,
            "ndvi_std_dev": 0.15,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
        },
        data_quality=DataQuality(
            source_image_count=source_images,
            usable_image_count=usable_images,
            valid_coverage=coverage,
        ),
        methodology=Methodology(
            dataset="COPERNICUS/S2_SR_HARMONIZED",
            resolution_m=10,
            composite_method="median",
            cloud_masking="QA60",
            index="NDVI = (B8 - B4) / (B8 + B4)",
        ),
        limitations=[],
        visualizations={},
    )


@pytest.mark.parametrize(
    "score",
    [0.80, 0.90, 1.00],
)
def test_high_quality(score):
    assert _get_quality_level(score, []) == "High"


@pytest.mark.parametrize(
    "score",
    [0.60, 0.65, 0.79],
)
def test_moderate_quality(score):
    assert _get_quality_level(score, []) == "Moderate"


@pytest.mark.parametrize(
    "score",
    [0.00, 0.20, 0.59],
)
def test_low_quality(score):
    assert _get_quality_level(score, []) == "Low"


def test_valid_ndvi_analysis():
    result = make_ndvi_result()

    validation = validate_analysis_result(result)

    assert validation.valid is True
    assert validation.quality_score == 1.0
    assert validation.quality_level == "High"
    assert validation.issues == []


def test_insufficient_image_count():
    result = make_ndvi_result(
        usable_images=3,
    )

    validation = validate_analysis_result(result)

    assert validation.valid is False
    assert validation.quality_score < 1.0
    assert validation.quality_level in {
        "Moderate",
        "Low",
    }

    assert any(
        check.name == "sufficient_image_count" and not check.passed
        for check in validation.checks
    )


def test_insufficient_spatial_coverage():
    result = make_ndvi_result(
        coverage=0.50,
    )

    validation = validate_analysis_result(result)

    assert validation.valid is False

    assert any(
        check.name == "sufficient_spatial_coverage" and not check.passed
        for check in validation.checks
    )


def test_invalid_ndvi_range():
    result = make_ndvi_result(
        mean_ndvi=1.5,
    )

    validation = validate_analysis_result(result)

    assert validation.valid is False

    assert any(
        check.name == "ndvi_range" and not check.passed for check in validation.checks
    )


def test_invalid_negative_ndvi_range():
    result = make_ndvi_result(
        mean_ndvi=-1.5,
    )

    validation = validate_analysis_result(result)

    assert validation.valid is False

    assert any(
        check.name == "ndvi_range" and not check.passed for check in validation.checks
    )


@pytest.mark.parametrize(
    "mean_ndvi",
    [-1.0, 0.0, 1.0],
)
def test_ndvi_boundary_values_are_valid(mean_ndvi):
    result = make_ndvi_result(
        mean_ndvi=mean_ndvi,
    )

    validation = validate_analysis_result(result)

    ndvi_check = next(
        check for check in validation.checks if check.name == "ndvi_range"
    )

    assert ndvi_check.passed is True


def test_missing_mean_ndvi():
    result = make_ndvi_result()

    del result.findings["mean_ndvi"]

    validation = validate_analysis_result(result)

    assert validation.valid is False

    ndvi_check = next(
        check for check in validation.checks if check.name == "ndvi_range"
    )

    assert ndvi_check.passed is False


def test_critical_validation_failure_caps_quality_level():
    result = make_ndvi_result(
        usable_images=3,
    )

    validation = validate_analysis_result(result)

    assert validation.quality_score == 0.8
    assert validation.quality_level == "Moderate"
    assert validation.valid is False


def make_landcover_result(
    source_images=100,
    usable_images=50,
    coverage=1.0,
    distribution=None,
):
    if distribution is None:
        distribution = {
            "water": 0.10,
            "trees": 0.20,
            "grass": 0.10,
            "flooded_vegetation": 0.05,
            "crops": 0.20,
            "shrub_and_scrub": 0.05,
            "built": 0.20,
            "bare": 0.05,
            "snow_and_ice": 0.05,
        }

    return AnalysisResult(
        analysis_type="landcover_analysis",
        findings={
            "landcover_distribution": distribution,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
        },
        data_quality=DataQuality(
            source_image_count=source_images,
            usable_image_count=usable_images,
            valid_coverage=coverage,
        ),
        methodology=Methodology(
            dataset="GOOGLE/DYNAMICWORLD/V1",
            resolution_m=10,
            composite_method="mode",
            cloud_masking=("Dynamic World quality-controlled observations"),
            index="Dynamic World land-cover label",
        ),
        limitations=[],
        visualizations={},
    )


def test_valid_landcover_analysis():
    result = make_landcover_result()

    validation = validate_analysis_result(result)

    assert validation.valid is True
    assert validation.quality_score == 1.0
    assert validation.quality_level == "High"
    assert validation.issues == []


def test_missing_landcover_distribution():
    result = make_landcover_result(
        distribution={},
    )

    validation = validate_analysis_result(result)

    assert validation.valid is False

    check = next(
        check
        for check in validation.checks
        if check.name == "landcover_distribution_valid"
    )

    assert check.passed is False


def test_invalid_landcover_proportion():
    distribution = {
        "water": 1.20,
        "trees": 0.00,
    }

    result = make_landcover_result(
        distribution=distribution,
    )

    validation = validate_analysis_result(result)

    assert validation.valid is False

    check = next(
        check
        for check in validation.checks
        if check.name == "landcover_distribution_valid"
    )

    assert check.passed is False


def test_landcover_distribution_does_not_sum_to_one():
    distribution = {
        "water": 0.20,
        "trees": 0.20,
        "built": 0.20,
    }

    result = make_landcover_result(
        distribution=distribution,
    )

    validation = validate_analysis_result(result)

    assert validation.valid is False

    check = next(
        check
        for check in validation.checks
        if check.name == "landcover_distribution_valid"
    )

    assert check.passed is False


def test_landcover_distribution_tolerance():
    distribution = {
        "water": 0.100,
        "trees": 0.200,
        "grass": 0.100,
        "flooded_vegetation": 0.050,
        "crops": 0.200,
        "shrub_and_scrub": 0.050,
        "built": 0.200,
        "bare": 0.050,
        "snow_and_ice": 0.101,
    }

    result = make_landcover_result(
        distribution=distribution,
    )

    validation = validate_analysis_result(result)

    check = next(
        check
        for check in validation.checks
        if check.name == "landcover_distribution_valid"
    )

    assert check.passed is False


def test_landcover_distribution_small_rounding_difference():
    distribution = {
        "water": 0.101,
        "trees": 0.200,
        "grass": 0.100,
        "flooded_vegetation": 0.050,
        "crops": 0.200,
        "shrub_and_scrub": 0.050,
        "built": 0.200,
        "bare": 0.050,
        "snow_and_ice": 0.050,
    }

    result = make_landcover_result(
        distribution=distribution,
    )

    validation = validate_analysis_result(result)

    check = next(
        check
        for check in validation.checks
        if check.name == "landcover_distribution_valid"
    )

    assert check.passed is True
