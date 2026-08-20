from __future__ import annotations

from typing import Any

import ee

from app.models.analysis import (
    AnalysisResult,
    DataQuality,
    Methodology,
)


S2_DATASET = "COPERNICUS/S2_SR_HARMONIZED"


def mask_s2_clouds(image: ee.Image) -> ee.Image:
    """
    Mask clouds and cirrus from a Sentinel-2 SR image using QA60.

    QA60:
        Bit 10 -> clouds
        Bit 11 -> cirrus

    The Sentinel-2 SR Harmonized documentation provides this
    QA60 masking approach.
    """

    qa = image.select("QA60")

    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11

    mask = (
        qa.bitwiseAnd(cloud_bit_mask)
        .eq(0)
        .And(
            qa.bitwiseAnd(cirrus_bit_mask)
            .eq(0)
        )
    )

    # Sentinel-2 SR values are scaled by 10000.
    return image.updateMask(mask).divide(10000)


def add_ndvi(image: ee.Image) -> ee.Image:
    """
    Add an NDVI band to a Sentinel-2 image.

    NDVI = (NIR - RED) / (NIR + RED)

    Sentinel-2:
        B8 = NIR
        B4 = RED
    """

    ndvi = image.normalizedDifference(
        ["B8", "B4"]
    ).rename("NDVI")

    return image.addBands(ndvi)


def build_ndvi_collection(
    aoi: ee.Geometry,
    start_date: str,
    end_date: str,
    max_cloud_percentage: float = 20.0,
) -> tuple[ee.ImageCollection, int]:
    """
    Build a cloud-masked Sentinel-2 NDVI collection.

    Returns:
        collection:
            Cloud-masked collection containing an NDVI band.

        source_image_count:
            Number of Sentinel-2 scenes before the
            scene-level cloud percentage filter.
    """

    source_collection = (
        ee.ImageCollection(S2_DATASET)
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
    )

    source_image_count = source_collection.size().getInfo()

    filtered_collection = (
        source_collection
        .filter(
            ee.Filter.lt(
                "CLOUDY_PIXEL_PERCENTAGE",
                max_cloud_percentage,
            )
        )
        .map(mask_s2_clouds)
        .map(add_ndvi)
    )

    return filtered_collection, source_image_count


def calculate_valid_coverage(
    image: ee.Image,
    aoi: ee.Geometry,
    scale: int = 10,
) -> float:
    """
    Estimate the fraction of the AOI containing valid NDVI pixels.

    Returns:
        Value between 0 and 1.
    """

    valid_mask = (
        image.select("NDVI")
        .mask()
        .rename("valid")
    )

    coverage = valid_mask.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=aoi,
        scale=scale,
        maxPixels=1e9,
        bestEffort=True,
    ).get("valid")

    coverage_value = coverage.getInfo()

    if coverage_value is None:
        return 0.0

    return float(coverage_value)


def calculate_ndvi_statistics(
    ndvi_composite: ee.Image,
    aoi: ee.Geometry,
    scale: int = 10,
) -> dict[str, float]:
    """
    Calculate regional NDVI statistics for the composite.
    """

    statistics = (
        ndvi_composite
        .select("NDVI")
        .reduceRegion(
            reducer=(
                ee.Reducer.mean()
                .combine(
                    reducer2=ee.Reducer.min(),
                    sharedInputs=True,
                )
                .combine(
                    reducer2=ee.Reducer.max(),
                    sharedInputs=True,
                )
                .combine(
                    reducer2=ee.Reducer.stdDev(),
                    sharedInputs=True,
                )
            ),
            geometry=aoi,
            scale=scale,
            maxPixels=1e9,
            bestEffort=True,
        )
        .getInfo()
    )

    return {
        "mean": float(statistics.get("NDVI_mean", 0.0)),
        "min": float(statistics.get("NDVI_min", 0.0)),
        "max": float(statistics.get("NDVI_max", 0.0)),
        "std_dev": float(statistics.get("NDVI_stdDev", 0.0)),
    }


def analyze_ndvi(
    aoi: ee.Geometry,
    start_date: str,
    end_date: str,
    max_cloud_percentage: float = 20.0,
    scale: int = 10,
) -> AnalysisResult:
    """
    Perform a basic regional NDVI analysis.

    Pipeline:

        Sentinel-2 SR Harmonized
            ↓
        AOI filtering
            ↓
        date filtering
            ↓
        scene cloud filtering
            ↓
        pixel cloud masking
            ↓
        NDVI calculation
            ↓
        median composite
            ↓
        regional statistics
            ↓
        structured AnalysisResult

    Args:
        aoi:
            Earth Engine geometry representing the AOI.

        start_date:
            Start date in YYYY-MM-DD format.

        end_date:
            End date in YYYY-MM-DD format.

        max_cloud_percentage:
            Maximum scene-level cloud percentage.

        scale:
            Analysis scale in meters.

    Returns:
        AnalysisResult containing NDVI statistics,
        data quality, methodology and limitations.
    """

    if not start_date:
        raise ValueError("start_date cannot be empty")

    if not end_date:
        raise ValueError("end_date cannot be empty")

    if scale <= 0:
        raise ValueError("scale must be greater than zero")

    if not 0 <= max_cloud_percentage <= 100:
        raise ValueError(
            "max_cloud_percentage must be between 0 and 100"
        )

    collection, source_image_count = build_ndvi_collection(
        aoi=aoi,
        start_date=start_date,
        end_date=end_date,
        max_cloud_percentage=max_cloud_percentage,
    )

    usable_image_count = collection.size().getInfo()

    if usable_image_count == 0:
        raise ValueError(
            "No usable Sentinel-2 images were found "
            "for the supplied AOI and date range."
        )

    # Create one representative image for the period.
    ndvi_composite = collection.median()

    statistics = calculate_ndvi_statistics(
        ndvi_composite=ndvi_composite,
        aoi=aoi,
        scale=scale,
    )

    valid_coverage = calculate_valid_coverage(
        image=ndvi_composite,
        aoi=aoi,
        scale=scale,
    )

    limitations = [
        "NDVI is a vegetation indicator and should not "
        "be interpreted as a direct measure of biomass.",
        "Cloud masking can leave areas with insufficient "
        "valid observations.",
        "The median composite represents the selected "
        "time period rather than a single observation.",
        "This PoC does not yet perform seasonal normalization "
        "or atmospheric-quality sensitivity analysis.",
    ]

    return AnalysisResult(
        analysis_type="ndvi_analysis",

        findings={
            "mean_ndvi": statistics["mean"],
            "minimum_ndvi": statistics["min"],
            "maximum_ndvi": statistics["max"],
            "ndvi_std_dev": statistics["std_dev"],
            "start_date": start_date,
            "end_date": end_date,
        },

        data_quality=DataQuality(
            source_image_count=source_image_count,
            usable_image_count=usable_image_count,
            valid_coverage=valid_coverage,
        ),

        methodology=Methodology(
            dataset=S2_DATASET,
            resolution_m=scale,
            composite_method="median",
            cloud_masking=(
                "QA60 cloud and cirrus masking + "
                "scene CLOUDY_PIXEL_PERCENTAGE filter"
            ),
            index="NDVI = (B8 - B4) / (B8 + B4)",
        ),

        limitations=limitations,

        visualizations={},
    )