import os
from dataclasses import dataclass

@dataclass
class Config:
    # RED Calculator defaults
    RED_CALCULATOR_DEFAULT_DRIVE = 100  # [%]
    RED_CALCULATOR_DEFAULT_EFFICIENCY = 100  # [%]
    RESOURCES_Path = "resources"
    LOGS_Path = "logs"

    # API Server configuration - Updated for Docker
    API_HOST = os.getenv("API_HOST", "0.0.0.0")  # Listen on all interfaces in container
    API_PORT = int(os.getenv("API_PORT", "5000"))
    API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"  # Disable debug in production

    # API Endpoints
    CALCULATE_ENDPOINT = "/calculate"
    HEALTH_ENDPOINT = "/health"
    PRESSURE_DROP_ENDPOINT = "/pressure-drop"

    # Default values for calculations
    DEFAULT_UVT215 = -1
    DEFAULT_D1LOG = 18.0

    # Application types
    APPLICATION_TYPES = ["Full Range", "Municipal EPA", "Dechlorination"]

    # Position types
    POSITION_TYPES = ["Vertical", "Horizontal"]

    # Lamp types
    LAMP_TYPES = ["Regular", "OzoneFree", "VUV"]

    # Flow units
    FLOW_UNITS = ["m3/h", "US GPM"]

    # MongoDB configuration - No sensitive defaults, must be set via environment
    mongo_uri = os.getenv("MONGO_URI")
    mongo_db = os.getenv("MONGO_DB", "CalcUsers")
    mongo_collection = os.getenv("MONGO_COLLECTION", "Calculator")


# Create global config instance
CONFIG = Config()
