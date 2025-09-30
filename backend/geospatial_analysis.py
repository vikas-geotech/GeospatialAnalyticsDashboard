import os
import ee
import geemap
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def convert_to_ee(file_path):
    """Convert uploaded GeoJSON file to Earth Engine geometry."""
    file_extension = os.path.splitext(file_path)[1].lower()
    try:
        if file_extension in ['.geojson', '.json']:
            ee_object = geemap.geojson_to_ee(file_path)
        else:
            raise ValueError("Unsupported file format. Supported: .geojson, .json")
        # If ee_object is a FeatureCollection, merge geometries into a single geometry
        if isinstance(ee_object, ee.FeatureCollection):
            geometry = ee_object.geometry()
            # Simplify the merged geometry to avoid complexity issues
            geometry = geometry.simplify(maxError=1)
            return geometry
        else:
            # If it's already a geometry, simplify it
            return ee_object.simplify(maxError=1)
    except Exception as e:
        raise ValueError(f"Failed to convert file to Earth Engine geometry: {str(e)}")

def get_collection(aoi, start_date, end_date, satellite, cloud_perc):
    """Fetch image collection for the specified satellite."""
    if satellite.lower() == "sentinel2":
        collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                      .filterBounds(aoi)
                      .filterDate(start_date, end_date)
                      .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloud_perc)))
        collection = collection.map(lambda img: img.multiply(0.0001)
                                   .copyProperties(img, img.propertyNames()))
        band_map = {"red": "B4", "green": "B3", "blue": "B2", "nir": "B8", "swir": "B11"}
        scale = 10
    elif satellite.lower() == "landsat8":
        collection = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                      .filterBounds(aoi)
                      .filterDate(start_date, end_date))
        collection = collection.map(lambda img: img.multiply(0.0000275).add(-0.2)
                                   .copyProperties(img, img.propertyNames()))
        band_map = {"red": "SR_B4", "green": "SR_B3", "blue": "SR_B2", "nir": "SR_B5", "swir": "SR_B6"}
        scale = 30
    else:
        raise ValueError("Unsupported satellite. Use: sentinel2, landsat8")
    return collection, band_map, scale

def calculate_indices(image, band_map):
    """Calculate NDVI and NDWI."""
    ndvi = image.normalizedDifference([band_map["nir"], band_map["red"]]).rename("NDVI")
    ndwi = image.normalizedDifference([band_map["nir"], band_map["green"]]).rename("NDWI")
    return ndvi, ndwi

def get_savi(image, band_map):
    """Calculate Soil Adjusted Vegetation Index (SAVI)."""
    return image.expression(
        "((NIR - RED) / (NIR + RED + L)) * (1 + L)",
        {"NIR": image.select(band_map["nir"]),
         "RED": image.select(band_map["red"]),
         "L": 0.5}
    ).rename("SAVI")

def get_evi(image, band_map):
    """Calculate Enhanced Vegetation Index (EVI)."""
    return image.expression(
        "2.5 * ((NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1))",
        {"NIR": image.select(band_map["nir"]),
         "RED": image.select(band_map["red"]),
         "BLUE": image.select(band_map["blue"])}
    ).rename("EVI")

def add_indices(image, band_map, indices=["NDVI", "NDWI", "SAVI", "EVI"]):
    """Add selected vegetation indices to the image."""
    result = image
    if "NDVI" in indices:
        ndvi, _ = calculate_indices(image, band_map)
        result = result.addBands(ndvi)
    if "NDWI" in indices:
        _, ndwi = calculate_indices(image, band_map)
        result = result.addBands(ndwi)
    if "SAVI" in indices:
        savi = get_savi(image, band_map)
        result = result.addBands(savi)
    if "EVI" in indices:
        evi = get_evi(image, band_map)
        result = result.addBands(evi)
    return result

def compute_time_series_stats(collection, aoi, scale, band_map, indices=["NDVI", "NDWI", "SAVI", "EVI"]):
    """Compute mean, min, max for each index over the time series."""
    def process_image(image):
        image = add_indices(image, band_map, indices)
        stats = {}
        for band in indices:
            stat_dict = image.select(band).reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    reducer2=ee.Reducer.minMax(), sharedInputs=True),
                geometry=aoi,
                scale=scale,
                bestEffort=True
            )
            stats[f"mean_{band}"] = ee.Number(stat_dict.get(f"{band}_mean")).format('%.3f')
            stats[f"min_{band}"] = ee.Number(stat_dict.get(f"{band}_min")).format('%.3f')
            stats[f"max_{band}"] = ee.Number(stat_dict.get(f"{band}_max")).format('%.3f')
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        return ee.Feature(None, {**stats, 'date': date})

    try:
        stats_features = collection.map(process_image).getInfo()['features']
        time_series_data = [
            {
                'date': f['properties']['date'],
                **{k: float(f['properties'][k]) if f['properties'][k] is not None else None
                   for k in f['properties'] if k != 'date'}
            }
            for f in stats_features
        ]
        return time_series_data
    except Exception as e:
        raise ValueError(f"Failed to compute time-series stats: {str(e)}")

def get_latest_image(collection, band_map, indices=["NDVI", "NDWI", "SAVI", "EVI"], aoi=None):
    """Retrieve the latest image with selected indices for visualization, clipped to AOI."""
    try:
        # Ensure AOI is provided
        if aoi is None:
            raise ValueError("AOI must be provided for clipping.")

        # Get unique dates in descending order
        times = collection.aggregate_array('system:time_start')
        dates = times.map(lambda t: ee.Date(t).format('YYYY-MM-dd'))
        unique_dates = ee.List(dates.distinct()).sort().reverse()  # Sort ascending and reverse for descending

        # Get the geometry of the AOI for coverage check
        overall_geom = aoi

        # Iterate through unique dates
        for date_str in unique_dates.getInfo():
            date = ee.Date(date_str)
            next_date = date.advance(1, 'day')
            daily_collection = collection.filterDate(date, next_date)
            size = daily_collection.size().getInfo()
            if size == 0:
                continue

            # Create a mosaic of images for the same date and clip to AOI
            mosaic = daily_collection.mosaic().clip(aoi)
            mask = mosaic.select(band_map["red"]).mask()
            coverage_fraction = mask.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=overall_geom,
                scale=collection.first().select(band_map["red"]).projection().nominalScale(),
                bestEffort=True
            ).get(band_map["red"])
            coverage = coverage_fraction.getInfo()
            if coverage is not None and coverage >= 0.95:
                latest_with_indices = add_indices(mosaic, band_map, indices)
                return latest_with_indices

        # Fallback to the latest image if no full coverage date is found
        latest = collection.sort('system:time_start', False).first()
        if latest is None:
            raise ValueError("No images found in the collection for the specified criteria.")
        latest_with_indices = add_indices(latest.clip(aoi), band_map, indices)
        return latest_with_indices
    except Exception as e:
        raise ValueError(f"Failed to retrieve latest image: {str(e)}")

def get_visualization_urls(image, band_map, indices=["NDVI", "NDWI", "SAVI", "EVI"]):
    """Generate visualization URLs for the latest image."""
    try:
        vis_params_rgb = {
            'bands': [band_map["swir"], band_map["nir"], band_map["red"]],
            'min': 0,
            'max': 0.3,
            'gamma': 1.4
        }
        vis_urls = {
            'rgb': image.visualize(**vis_params_rgb).getMapId()['tile_fetcher'].url_format
        }
        for index in indices:
            vis_params_index = {
                'bands': [index],
                'min': -1,
                'max': 1,
                'palette': ['red', 'yellow', 'green']
            }
            vis_urls[index] = image.visualize(**vis_params_index).getMapId()['tile_fetcher'].url_format
        return vis_urls
    except Exception as e:
        raise ValueError(f"Failed to generate visualization URLs: {str(e)}")

def compute_stats(image, aoi, scale, indices=["NDVI", "NDWI", "SAVI", "EVI"]):
    """Compute summary statistics for the specified indices in the latest image."""
    stats = {}
    try:
        for band in indices:
            mean_val = image.select(band).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=scale,
                bestEffort=True
            ).get(band).getInfo()
            stats[f"mean_{band}"] = round(mean_val, 3) if mean_val is not None else None

        # Vegetation cover (% area with NDVI > 0.3)
        if "NDVI" in indices:
            veg_cover = image.select("NDVI").gt(0.3).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=scale,
                bestEffort=True
            ).get("NDVI").getInfo()
            stats["veg_cover_percent"] = round(veg_cover * 100, 1) if veg_cover is not None else None
        else:
            stats["veg_cover_percent"] = None

        # Total area with error margin
        area = aoi.area(maxError=1).divide(1e6).getInfo()  # Convert to km²
        stats["total_area_km2"] = round(area, 2) if area is not None else None

        # Healthy areas (NDVI > 0.5)
        if "NDVI" in indices:
            healthy_area = image.select("NDVI").gt(0.5).multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=aoi,
                scale=scale,
                bestEffort=True
            ).get("NDVI").getInfo()
            stats["healthy_area_km2"] = round(healthy_area / 1e6, 2) if healthy_area is not None else None
        else:
            stats["healthy_area_km2"] = None

        return stats
    except Exception as e:
        raise ValueError(f"Failed to compute stats: {str(e)}")

def start_automation(file_path, start_date, end_date, satellite="sentinel2", cloud_percentage=15, indices=["NDVI", "NDWI", "SAVI", "EVI"]):
    """Main function to process geospatial analysis."""
    # Initialize GEE
    try:
        service_account = os.getenv('SERVICE_ACCOUNT_EMAIL')
        private_key = os.getenv('PRIVATE_KEY')
        if not service_account or not private_key:
            raise ValueError("Environment variables SERVICE_ACCOUNT_EMAIL or PRIVATE_KEY not set")
        credentials = ee.ServiceAccountCredentials(service_account, key_data=private_key)
        ee.Initialize(credentials)
    except Exception as e:
        raise ValueError(f"Failed to initialize Earth Engine: {str(e)}")

    # Load AOI
    region = convert_to_ee(file_path)

    # Get satellite collection
    collection, band_map, scale = get_collection(region, start_date, end_date, satellite, cloud_percentage)

    # Compute time-series statistics
    time_series_stats = compute_time_series_stats(collection, region, scale, band_map, indices)

    # Get latest image for visualization, passing the region (AOI)
    latest_image = get_latest_image(collection, band_map, indices, aoi=region)

    # Compute additional stats (e.g., vegetation cover, total area)
    stats = compute_stats(latest_image, region, scale, indices)

    # Generate visualization URLs
    vis_urls = get_visualization_urls(latest_image, band_map, indices)

    # Format output for frontend
    output = {
        'time_series': time_series_stats,
        'stats': stats,
        'visualization': vis_urls
    }

    return json.dumps(output)