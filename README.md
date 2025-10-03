# 🌍 Geospatial Analytics Dashboard

A powerful web-based geospatial analytics platform that leverages Google Earth Engine to analyze satellite imagery and calculate vegetation indices over time. Upload your area of interest and get instant insights into vegetation health, water content, and environmental changes.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![Google Earth Engine](https://img.shields.io/badge/Google%20Earth%20Engine-Enabled-orange.svg)


## ✨ Features

- **Multi-Satellite Support**: Analyze data from Sentinel-2 and Landsat-8 satellites
- **Vegetation Indices**: Calculate NDVI, EVI, NDWI, and SAVI indices
- **Time Series Analysis**: Track changes over custom date ranges
- **Interactive Mapping**: Visualize results on an interactive Leaflet map
- **Cloud Filtering**: Control cloud cover percentage for cleaner analysis
- **Real-time Visualization**: View false-color imagery and index overlays
- **Statistical Insights**: Get mean, min, max values and vegetation cover percentages
- **Export Results**: Download analysis results as text files
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## 🚀 Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.8 or higher
- pip (Python package manager)
- Google Earth Engine account ([Sign up here](https://earthengine.google.com/signup/))
- GEE Service Account credentials (JSON key file)

## 📦 Installation

### 1. Clone the Repository

\`\`\`bash
git clone https://github.com/vikas-geotech/GeospatialAnalyticsDashboard.git
cd geospatial-analytics-dashboard
\`\`\`

### 2. Create Virtual Environment

\`\`\`bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
\`\`\`

### 3. Install Dependencies

\`\`\`bash
pip install -r requirements.txt
\`\`\`

Create a `requirements.txt` file with the following content:

\`\`\`txt
flask==2.3.0
flask-cors==4.0.0
earthengine-api==0.1.350
geemap==0.30.0
flasgger==0.9.7
\`\`\`

### 4. Configure Google Earth Engine

1. Create a Google Cloud Project and enable the Earth Engine API
2. Create a Service Account and download the JSON key file
3. Place the JSON key file in the project root directory
4. Update the credentials in `geospatial_analysis.py`:


## 🗂️ Project Structure

\`\`\`
geospatial-analytics-dashboard/
│
├── app.py                          # Flask application entry point
├── geospatial_analysis.py          # Core GEE analysis logic
├── templates/
│   └── index.html                  # Frontend dashboard
├── uploads/                        # Temporary file storage (auto-created)
├── requirements.txt                # Python dependencies
├── your-key-file.json             # GEE service account credentials (not in repo)
├── .gitignore                     # Git ignore file
└── README.md                      # This file
\`\`\`

## 🎯 Usage

### 1. Start the Application

\`\`\`bash
python app.py
\`\`\`

The application will start on `http://localhost:8000`

### 2. Upload Your Area of Interest

1. Prepare a GeoJSON file (`.geojson` or `.json`) containing your area of interest
2. Click the upload box and select your file
3. The area will be displayed on the map

### 3. Configure Analysis Parameters

- **Satellite Source**: Choose between Sentinel-2 (10m resolution) or Landsat-8 (30m resolution)
- **Date Range**: Select start and end dates for your analysis
- **Cloud Cover**: Set maximum acceptable cloud cover percentage (0-100%)
- **Indices**: Select which vegetation indices to calculate (NDVI, EVI, NDWI, SAVI)

### 4. Run Analysis

Click the "🚀 Start Analysis" button and wait for processing to complete. Results will include:

- Time series charts showing index values over time
- Statistical summaries (mean, min, max values)
- Vegetation cover percentage
- Total and healthy area calculations
- Interactive map layers for visualization

### 5. Explore Results

- Toggle different map layers (RGB imagery, NDVI, EVI, NDWI, SAVI)
- Click on the map to see pixel-level information
- Switch between different indices in the time series chart
- Download results as a text file

## 🔧 API Endpoints

### POST `/api/analyze`

Processes geospatial analysis for uploaded area.

**Request:**
- `file`: GeoJSON file (multipart/form-data)
- `startDate`: Start date (YYYY-MM-DD)
- `endDate`: End date (YYYY-MM-DD)
- `satellite`: Satellite source ("sentinel2" or "landsat8")
- `cloudPercentage`: Maximum cloud cover (0-100)
- `indices`: JSON array of indices (["NDVI", "EVI", "NDWI", "SAVI"])

**Response:**
\`\`\`json
{
  "message": "Analysis complete",
  "status": 200,
  "data": {
    "time_series": [...],
    "stats": {...},
    "visualization": {...}
  }
}
\`\`\`

## 🌱 Vegetation Indices Explained

- **NDVI** (Normalized Difference Vegetation Index): Measures vegetation greenness and health
- **EVI** (Enhanced Vegetation Index): Improved sensitivity in high biomass regions
- **NDWI** (Normalized Difference Water Index): Detects water content in vegetation
- **SAVI** (Soil Adjusted Vegetation Index): Minimizes soil brightness influences

## 🔒 Security Notes

- **Never commit your GEE credentials** to version control
- Add `*.json` (credential files) to `.gitignore`
- Use environment variables for sensitive configuration in production
- Implement rate limiting for the API endpoint
- Validate and sanitize all user inputs

## 📝 .gitignore

Create a `.gitignore` file with:

\`\`\`
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Google Earth Engine credentials
*.json
!requirements.txt

# Uploads
uploads/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
\`\`\`

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## 🙏 Acknowledgments

- [Google Earth Engine](https://earthengine.google.com/) for satellite imagery and processing
- [Leaflet](https://leafletjs.com/) for interactive mapping
- [Chart.js](https://www.chartjs.org/) for data visualization
- [Flask](https://flask.palletsprojects.com/) for the web framework

## 📧 Contact

Vikas Kumar Gupta -  [Email-ID] vkgupta0495@gmail.com

Project Link: https://github.com/vikas-geotech/GeospatialAnalyticsDashboard

## 🐛 Known Issues

- Large GeoJSON files (>5MB) may cause timeout issues
- Complex geometries may need simplification for faster processing
- First analysis may take longer due to GEE initialization

## 🔮 Future Enhancements

- [ ] Support for additional satellites (Landsat series, MODIS, etc..)
- [ ] Export results as csv
- [ ] User authentication and saved analyses
- [ ] Advanced filtering and cloud masking options
- [ ] Integration with other environmental datasets
\`\`\`

This README provides comprehensive documentation for your geospatial analytics project. It includes installation instructions, usage guidelines, API documentation, and important security notes about handling Google Earth Engine credentials. Make sure to update the placeholder information (like your GitHub username, email, and service account details) before publishing!