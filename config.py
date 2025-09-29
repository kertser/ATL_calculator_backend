from dataclasses import dataclass


@dataclass
class Config:
    # RED Calculator defaults
    RED_CALCULATOR_DEFAULT_DRIVE = 100  # [%]
    RED_CALCULATOR_DEFAULT_EFFICIENCY = 100  # [%]
    RESOURCES_Path = "resources"
    LOGS_Path = "logs"

    # API Server configuration
    API_HOST = "localhost"
    API_PORT = 5000
    API_DEBUG = True

    # API Endpoints
    CALCULATE_ENDPOINT = "/calculate"

    # Default values for calculations
    DEFAULT_UVT215 = -1
    DEFAULT_D1LOG = 18.0

    # Application types
    APPLICATION_TYPES = ["Full Range", "Municipal", "Dechlorination"]

    # Position types
    POSITION_TYPES = ["Vertical", "Horizontal"]

    # Lamp types
    LAMP_TYPES = ["Regular", "OzoneFree", "VUV"]

    # Flow units
    FLOW_UNITS = ["m3/h", "US GPM"]


# Create global config instance
CONFIG = Config()
