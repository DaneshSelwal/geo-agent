import pytest
from unittest.mock import MagicMock, patch

from app.analysis.vegetation import (
    analyze_ndvi,
    add_ndvi,
    build_ndvi_collection,
    calculate_ndvi_statistics,
    calculate_valid_coverage,
    mask_s2_clouds,
    S2_DATASET,
)
from app.models.analysis import AnalysisResult, DataQuality, Methodology


def test_mask_s2_clouds():
    mock_image = MagicMock()
    mock_qa = MagicMock()
    mock_image.select.return_value = mock_qa

    mock_mask_1 = MagicMock()
    mock_qa.bitwiseAnd.return_value.eq.return_value = mock_mask_1

    mock_mask_2 = MagicMock()
    mock_mask_1.And.return_value = mock_mask_2

    mock_updated_mask = MagicMock()
    mock_image.updateMask.return_value = mock_updated_mask

    result = mask_s2_clouds(mock_image)

    mock_image.select.assert_called_once_with("QA60")
    # 1 << 10 = 1024, 1 << 11 = 2048
    mock_qa.bitwiseAnd.assert_any_call(1024)
    mock_qa.bitwiseAnd.assert_any_call(2048)

    mock_image.updateMask.assert_called_once_with(mock_mask_2)
    mock_updated_mask.divide.assert_called_once_with(10000)
    assert result == mock_updated_mask.divide.return_value


def test_add_ndvi():
    mock_image = MagicMock()
    mock_ndvi = MagicMock()

    mock_image.normalizedDifference.return_value.rename.return_value = (
        mock_ndvi
    )

    result = add_ndvi(mock_image)

    mock_image.normalizedDifference.assert_called_once_with(["B8", "B4"])
    rename_mock = mock_image.normalizedDifference.return_value.rename
    rename_mock.assert_called_once_with("NDVI")

    mock_image.addBands.assert_called_once_with(mock_ndvi)
    assert result == mock_image.addBands.return_value


@patch("app.analysis.vegetation.ee")
def test_build_ndvi_collection(mock_ee):
    mock_aoi = MagicMock()

    mock_collection = MagicMock()
    mock_ee.ImageCollection.return_value = mock_collection

    mock_filtered_bounds = MagicMock()
    mock_collection.filterBounds.return_value = mock_filtered_bounds

    mock_filtered_date = MagicMock()
    mock_filtered_bounds.filterDate.return_value = mock_filtered_date

    mock_size = MagicMock()
    mock_filtered_date.size.return_value = mock_size

    mock_filter_cloudy = MagicMock()
    mock_filtered_date.filter.return_value = mock_filter_cloudy

    mock_mapped_mask = MagicMock()
    mock_filter_cloudy.map.return_value = mock_mapped_mask

    mock_mapped_ndvi = MagicMock()
    mock_mapped_mask.map.return_value = mock_mapped_ndvi

    mock_filter_lt = MagicMock()
    mock_ee.Filter.lt.return_value = mock_filter_lt

    collection, source_count = build_ndvi_collection(
        aoi=mock_aoi,
        start_date="2023-01-01",
        end_date="2023-12-31",
        max_cloud_percentage=15.0,
    )

    mock_ee.ImageCollection.assert_called_once_with(S2_DATASET)
    mock_collection.filterBounds.assert_called_once_with(mock_aoi)
    mock_filtered_bounds.filterDate.assert_called_once_with(
        "2023-01-01", "2023-12-31"
    )

    mock_ee.Filter.lt.assert_called_once_with("CLOUDY_PIXEL_PERCENTAGE", 15.0)
    mock_filtered_date.filter.assert_called_once_with(mock_filter_lt)

    mock_filter_cloudy.map.assert_called_once_with(mask_s2_clouds)
    mock_mapped_mask.map.assert_called_once_with(add_ndvi)

    assert collection == mock_mapped_ndvi
    assert source_count == mock_size


@patch("app.analysis.vegetation.ee")
def test_calculate_valid_coverage(mock_ee):
    mock_image = MagicMock()
    mock_aoi = MagicMock()

    mock_valid_mask = MagicMock()
    mock_sel_mask = mock_image.select.return_value.mask
    mock_sel_mask.return_value.rename.return_value = mock_valid_mask

    mock_reducer_mean = MagicMock()
    mock_ee.Reducer.mean.return_value = mock_reducer_mean

    mock_reduced = MagicMock()
    mock_valid_mask.reduceRegion.return_value = mock_reduced

    mock_get = MagicMock()
    mock_reduced.get.return_value = mock_get

    mock_ee_number = MagicMock()
    mock_ee.Number.return_value = mock_ee_number

    result = calculate_valid_coverage(mock_image, mock_aoi, scale=20)

    mock_image.select.assert_called_once_with("NDVI")
    mock_image.select.return_value.mask.assert_called_once()
    mask_rename = mock_image.select.return_value.mask.return_value.rename
    mask_rename.assert_called_once_with("valid")

    mock_valid_mask.reduceRegion.assert_called_once_with(
        reducer=mock_reducer_mean,
        geometry=mock_aoi,
        scale=20,
        maxPixels=1e9,
        bestEffort=True,
    )
    mock_reduced.get.assert_called_once_with("valid")
    mock_ee.Number.assert_called_once_with(mock_get)

    assert result == mock_ee_number


@patch("app.analysis.vegetation.ee")
def test_calculate_ndvi_statistics(mock_ee):
    mock_composite = MagicMock()
    mock_aoi = MagicMock()

    # Reducers
    mock_mean = MagicMock()
    mock_min = MagicMock()
    mock_max = MagicMock()
    mock_stddev = MagicMock()

    mock_ee.Reducer.mean.return_value = mock_mean
    mock_ee.Reducer.min.return_value = mock_min
    mock_ee.Reducer.max.return_value = mock_max
    mock_ee.Reducer.stdDev.return_value = mock_stddev

    mock_combine_1 = MagicMock()
    mock_mean.combine.return_value = mock_combine_1

    mock_combine_2 = MagicMock()
    mock_combine_1.combine.return_value = mock_combine_2

    mock_combine_3 = MagicMock()
    mock_combine_2.combine.return_value = mock_combine_3

    mock_reduced = MagicMock()
    mock_comp_sel = mock_composite.select.return_value
    mock_comp_sel.reduceRegion.return_value = mock_reduced

    # Values
    def mock_contains(key):
        return True

    mock_reduced.contains.side_effect = mock_contains
    mock_reduced.getNumber.side_effect = lambda key: f"value_for_{key}"

    mock_if = MagicMock()
    mock_ee.Algorithms.If.side_effect = lambda cond, t, f: t

    mock_dict = MagicMock()
    mock_ee.Dictionary.return_value = mock_dict

    result = calculate_ndvi_statistics(mock_composite, mock_aoi, scale=15)

    mock_composite.select.assert_called_once_with("NDVI")
    mock_mean.combine.assert_called_once_with(
        reducer2=mock_min, sharedInputs=True
    )
    mock_combine_1.combine.assert_called_once_with(
        reducer2=mock_max, sharedInputs=True
    )
    mock_combine_2.combine.assert_called_once_with(
        reducer2=mock_stddev, sharedInputs=True
    )

    mock_composite.select.return_value.reduceRegion.assert_called_once_with(
        reducer=mock_combine_3,
        geometry=mock_aoi,
        scale=15,
        maxPixels=1e9,
        bestEffort=True,
    )

    mock_ee.Dictionary.assert_called_once_with(
        {
            "mean": "value_for_NDVI_mean",
            "min": "value_for_NDVI_min",
            "max": "value_for_NDVI_max",
            "std_dev": "value_for_NDVI_stdDev",
        }
    )
    assert result == mock_dict


def test_analyze_ndvi_invalid_inputs():
    mock_aoi = MagicMock()

    with pytest.raises(ValueError, match="start_date cannot be empty"):
        analyze_ndvi(mock_aoi, start_date="", end_date="2023-12-31")

    with pytest.raises(ValueError, match="end_date cannot be empty"):
        analyze_ndvi(mock_aoi, start_date="2023-01-01", end_date="")

    with pytest.raises(ValueError, match="scale must be greater than zero"):
        analyze_ndvi(
            mock_aoi, start_date="2023-01-01", end_date="2023-12-31", scale=0
        )

    with pytest.raises(
        ValueError, match="max_cloud_percentage must be between 0 and 100"
    ):
        analyze_ndvi(
            mock_aoi,
            start_date="2023-01-01",
            end_date="2023-12-31",
            max_cloud_percentage=-1,
        )

    with pytest.raises(
        ValueError, match="max_cloud_percentage must be between 0 and 100"
    ):
        analyze_ndvi(
            mock_aoi,
            start_date="2023-01-01",
            end_date="2023-12-31",
            max_cloud_percentage=101,
        )


@patch("app.analysis.vegetation.ee")
@patch("app.analysis.vegetation.build_ndvi_collection")
def test_analyze_ndvi_no_images(mock_build, mock_ee):
    mock_aoi = MagicMock()
    mock_collection = MagicMock()
    mock_source_count = MagicMock()
    mock_build.return_value = (mock_collection, mock_source_count)

    mock_dict = MagicMock()
    mock_ee.Dictionary.return_value = mock_dict

    # Return 0 for 'usable'
    mock_dict.getInfo.return_value = {"source": 10, "usable": 0}

    with pytest.raises(
        ValueError, match="No usable Sentinel-2 images were found"
    ):
        analyze_ndvi(mock_aoi, start_date="2023-01-01", end_date="2023-12-31")


@patch("app.analysis.vegetation.ee")
@patch("app.analysis.vegetation.calculate_valid_coverage")
@patch("app.analysis.vegetation.calculate_ndvi_statistics")
@patch("app.analysis.vegetation.build_ndvi_collection")
def test_analyze_ndvi_success(
    mock_build, mock_calc_stats, mock_calc_coverage, mock_ee
):
    mock_aoi = MagicMock()
    mock_collection = MagicMock()
    mock_source_count = MagicMock()
    mock_build.return_value = (mock_collection, mock_source_count)

    mock_composite = MagicMock()
    mock_collection.median.return_value = mock_composite

    mock_stats_dict = MagicMock()
    mock_calc_stats.return_value = mock_stats_dict

    mock_coverage_num = MagicMock()
    mock_calc_coverage.return_value = mock_coverage_num

    mock_dict_1 = MagicMock()
    mock_dict_2 = MagicMock()

    # Return mock dictionaries for the two ee.Dictionary calls
    mock_ee.Dictionary.side_effect = [mock_dict_1, mock_dict_2]

    mock_dict_1.getInfo.return_value = {"source": 15, "usable": 12}

    mock_dict_2.getInfo.return_value = {
        "statistics": {
            "mean": 0.45,
            "min": -0.1,
            "max": 0.8,
            "std_dev": 0.15,
        },
        "valid_coverage": 0.95,
    }

    result = analyze_ndvi(
        mock_aoi,
        start_date="2023-01-01",
        end_date="2023-12-31",
        max_cloud_percentage=25.0,
        scale=20,
    )

    # Verify build is called
    mock_build.assert_called_once_with(
        aoi=mock_aoi,
        start_date="2023-01-01",
        end_date="2023-12-31",
        max_cloud_percentage=25.0,
    )

    # Verify median composite is created
    mock_collection.median.assert_called_once()

    # Verify statistics calculation
    mock_calc_stats.assert_called_once_with(
        ndvi_composite=mock_composite, aoi=mock_aoi, scale=20
    )

    # Verify coverage calculation
    mock_calc_coverage.assert_called_once_with(
        image=mock_composite, aoi=mock_aoi, scale=20
    )

    # Check AnalysisResult construction
    assert isinstance(result, AnalysisResult)
    assert result.analysis_type == "ndvi_analysis"
    assert result.findings["mean_ndvi"] == 0.45
    assert result.findings["minimum_ndvi"] == -0.1
    assert result.findings["maximum_ndvi"] == 0.8
    assert result.findings["ndvi_std_dev"] == 0.15
    assert result.findings["start_date"] == "2023-01-01"
    assert result.findings["end_date"] == "2023-12-31"

    assert isinstance(result.data_quality, DataQuality)
    assert result.data_quality.source_image_count == 15
    assert result.data_quality.usable_image_count == 12
    assert result.data_quality.valid_coverage == 0.95

    assert isinstance(result.methodology, Methodology)
    assert result.methodology.dataset == S2_DATASET
    assert result.methodology.resolution_m == 20
    assert result.methodology.composite_method == "median"

    assert len(result.limitations) == 4
