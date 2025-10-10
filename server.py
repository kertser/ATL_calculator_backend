from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional, Union, List
import logging
from contextlib import asynccontextmanager
from calculator import REDLibrary
from pymongo import MongoClient
from datetime import datetime
from config import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize calculator globally
calculator = None

def init_calculator():
    """Initialize the RED calculator"""
    global calculator
    try:
        calculator = REDLibrary()
        logging.info("Calculator initialized successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize calculator: {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not init_calculator():
        logging.error("Failed to initialize calculator during startup")
        raise RuntimeError("Calculator initialization failed")

    yield

    # Shutdown (cleanup if needed)
    logging.info("Application shutting down")

# Pydantic models for request/response validation
class CalculationRequest(BaseModel):
    Application: str = Field(..., description="Application type")
    Module: str = Field(..., description="Module identifier")
    Model: str = Field(..., description="Model identifier")
    Branch: str = Field(..., description="Branch identifier")
    Position: str = Field(..., description="Position type")
    Lamp_Type: str = Field(..., alias="Lamp Type", description="Lamp type")
    Efficiency: float = Field(..., ge=0, le=100, description="Efficiency percentage")
    Relative_Drive: float = Field(..., alias="Relative Drive", ge=0, le=100, description="Relative drive percentage")
    UVT_1cm_254nm: float = Field(..., alias="UVT-1cm@254nm", ge=0, le=100, description="UVT at 254nm")
    UVT_1cm_215nm: Optional[float] = Field(None, alias="UVT-1cm@215nm", ge=0, le=100, description="UVT at 215nm")
    Flow_Rate: float = Field(..., alias="Flow Rate", gt=0, description="Flow rate")
    Flow_Units: str = Field(..., alias="Flow Units", description="Flow rate units")
    D_1Log: Optional[float] = Field(None, alias="D-1Log", description="D-1Log value")
    Pathogen: Optional[str] = Field(None, description="Pathogen type")

    @field_validator('Application')
    def validate_application(v):
        if v not in CONFIG.APPLICATION_TYPES:
            raise ValueError(f"Application must be one of: {', '.join(CONFIG.APPLICATION_TYPES)}")
        return v

    @field_validator('Position')
    def validate_position(v):
        if v not in CONFIG.POSITION_TYPES:
            raise ValueError(f"Position must be one of: {', '.join(CONFIG.POSITION_TYPES)}")
        return v

    @field_validator('Lamp_Type')
    def validate_lamp_type(v):
        if v not in CONFIG.LAMP_TYPES:
            raise ValueError(f"Lamp Type must be one of: {', '.join(CONFIG.LAMP_TYPES)}")
        return v

    @field_validator('Flow_Units')
    def validate_flow_units(v):
        if v not in CONFIG.FLOW_UNITS:
            raise ValueError(f"Flow Units must be one of: {', '.join(CONFIG.FLOW_UNITS)}")
        return v

class CalculationResponse(BaseModel):
    Reduction_Equivalent_Dose: float = Field(..., alias="Reduction Equivalent Dose")
    Pressure_Drop: float = Field(..., alias="Pressure Drop")
    Maximum_Electrical_Power: float = Field(..., alias="Maximum Electrical Power")
    Average_Lamp_Power_Consumption: float = Field(..., alias="Average Lamp Power Consumption")
    Expected_LI: int = Field(..., alias="Expected LI")
    status: str
    calculation_details: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    calculator_initialized: bool

class ParameterRangesResponse(BaseModel):
    system_type: str
    ranges: Dict[str, Any]
    status: str

class SupportedSystemsResponse(BaseModel):
    systems: Dict[str, List[str]]
    status: str

class LoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class LoginResponse(BaseModel):
    status: str
    message: str
    role: Optional[str] = None
    calculator_type: Optional[str] = None

class PressureDropRequest(BaseModel):
    system_type: str = Field(..., description="System type")
    flow_rate: float = Field(..., gt=0, description="Flow rate")

class PressureDropResponse(BaseModel):
    status: str
    pressure_drop: float = Field(..., description="Calculated pressure drop")
    unit: str = Field(..., description="Unit of the pressure drop")
    details: Optional[Dict[str, Any]] = None

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="UV System Calculator API",
    description="REST API for UV system calculations including RED, head loss, and power consumption",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def convert_to_system_type(module: str, model: str) -> str:
    """Convert Module and Model to System Type format"""
    return f"{module}-{model}"

# MongoDB connection function
def get_mongo_client():
    """Get MongoDB client connection"""
    try:
        client = MongoClient(CONFIG.mongo_uri)
        return client
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        return None

@app.get(CONFIG.HEALTH_ENDPOINT, response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        calculator_initialized=calculator is not None
    )

@app.post(CONFIG.CALCULATE_ENDPOINT, response_model=CalculationResponse)
async def calculate(request: CalculationRequest):
    """Main calculation endpoint"""
    try:
        # Check if calculator is initialized
        if calculator is None:
            raise HTTPException(
                status_code=500,
                detail="Calculator not initialized"
            )

        # Convert Module + Model to System Type
        system_type = convert_to_system_type(request.Module, request.Model)

        # Extract parameters for calculation
        flow_rate = request.Flow_Rate
        uvt_254 = request.UVT_1cm_254nm
        uvt_215 = request.UVT_1cm_215nm or CONFIG.DEFAULT_UVT215
        d1_log = request.D_1Log or CONFIG.DEFAULT_D1LOG
        efficiency = request.Efficiency
        relative_drive = request.Relative_Drive

        # Prepare settings for calculation
        power_settings = {"all_lamps": relative_drive}
        efficiency_settings = {"all_lamps": efficiency}

        # Calculate RED
        red_result = calculator.calculate_red(
            system_type=system_type,
            flow=flow_rate,
            uvt=uvt_254,
            uvt215=uvt_215,
            d1_log=d1_log,
            power_settings=power_settings,
            efficiency_settings=efficiency_settings
        )

        # Check if calculation was successful
        if not red_result or red_result.get("status") != "success":
            error_info = red_result.get("error", {}) if red_result else {}
            raise HTTPException(
                status_code=400,
                detail={
                    "error": error_info.get("message", "Calculation failed"),
                    "details": error_info
                }
            )

        # Calculate pressure drop
        pressure_drop_result = calculator.calculate_pressure_drop(
            system_type=system_type,
            flow=flow_rate
        )

        pressure_drop = -1.0
        if pressure_drop_result and pressure_drop_result.get("status") == "success":
            pressure_drop = pressure_drop_result["result"]

        # Calculate Maximum Electrical Power = lamp_power * number_of_lamps
        max_electrical_power = -1.0
        details = red_result.get("details", {})
        lamp_power = details.get("lamp_power_watts", -1.0)
        n_lamps = details.get("number_of_lamps", 0)
        if lamp_power > 0 and n_lamps > 0:
            max_electrical_power = lamp_power * n_lamps

        # Average Lamp Power Consumption is just lamp_power
        avg_lamp_power_consumption = lamp_power if lamp_power > 0 else -1.0

        # Expected LI (Log Inactivation) = RED / D1Log (rounded to integer)
        expected_li = -1
        red_value = red_result.get("result", 0)
        if red_value > 0 and d1_log > 0:
            expected_li = round(red_value / d1_log)

        # Prepare response
        return CalculationResponse(
            **{
                "Reduction Equivalent Dose": red_result["result"],
                "Pressure Drop": pressure_drop,
                "Maximum Electrical Power": max_electrical_power,
                "Average Lamp Power Consumption": avg_lamp_power_consumption,
                "Expected LI": expected_li,
                "status": "success",
                "calculation_details": red_result.get("details", {})
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in calculate endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/system/{system_type}/ranges", response_model=ParameterRangesResponse)
async def get_parameter_ranges(system_type: str):
    """Get parameter ranges for a specific system"""
    try:
        if calculator is None:
            raise HTTPException(
                status_code=500,
                detail="Calculator not initialized"
            )

        ranges = calculator.get_parameter_ranges(system_type)
        if ranges is None:
            raise HTTPException(
                status_code=404,
                detail=f"System type '{system_type}' not found"
            )

        return ParameterRangesResponse(
            system_type=system_type,
            ranges=ranges,
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting parameter ranges: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting parameter ranges: {str(e)}"
        )

@app.get("/systems/supported", response_model=SupportedSystemsResponse)
async def get_supported_systems():
    """Get list of supported systems grouped by series"""
    try:
        if calculator is None:
            raise HTTPException(
                status_code=500,
                detail="Calculator not initialized"
            )

        systems = calculator.get_grouped_supported_systems()
        if not systems:
            raise HTTPException(
                status_code=404,
                detail="No supported systems found"
            )

        return SupportedSystemsResponse(
            systems=systems,
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting supported systems: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting supported systems: {str(e)}"
        )

@app.post(CONFIG.PRESSURE_DROP_ENDPOINT, response_model=PressureDropResponse)
async def calculate_pressure_drop(request: PressureDropRequest):
    """Calculate pressure drop for a given system type and flow rate"""
    try:
        if calculator is None:
            raise HTTPException(
                status_code=500,
                detail="Calculator not initialized"
            )

        result = calculator.calculate_pressure_drop(
            system_type=request.system_type,
            flow=request.flow_rate
        )

        if not result or result.get("status") != "success":
            error_info = result.get("error", {}) if result else {}
            raise HTTPException(
                status_code=400,
                detail={
                    "error": error_info.get("message", "Pressure drop calculation failed"),
                    "details": error_info
                }
            )

        return PressureDropResponse(
            status="success",
            pressure_drop=result["result"],
            unit=result["unit"],
            details=result.get("details", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in pressure drop endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# MongoDB Login endpoint
@app.post(CONFIG.LOGIN_ENDPOINT, response_model=LoginResponse)
async def login(request: LoginRequest):
    """User authentication endpoint"""
    client = None
    try:
        # Connect to MongoDB
        client = get_mongo_client()
        if client is None:
            raise HTTPException(
                status_code=500,
                detail="Database connection failed"
            )

        db = client.get_database(CONFIG.mongo_db)
        records = db[CONFIG.mongo_collection]

        # Find user by username
        user = list(records.find({'UserName': request.username}))

        if not user:
            return LoginResponse(
                status="error",
                message="Wrong Login Name"
            )

        user_data = user[0]
        stored_password = user_data.get('Password')
        expiration_date = user_data.get('Expiration Date')
        role = user_data.get('Role')

        # SECURITY WARNING: Plain text password comparison
        # TODO: Implement proper password hashing (bcrypt, argon2, etc.)
        if request.password != stored_password:
            return LoginResponse(
                status="error",
                message="Wrong Password"
            )

        # Check expiration date
        today = datetime.now().strftime("%d-%b-%Y")
        today_date = datetime.strptime(today, "%d-%b-%Y").date()
        exp_date = datetime.strptime(expiration_date, "%d-%b-%Y").date()

        if today_date > exp_date:
            return LoginResponse(
                status="error",
                message="Password Date Expired"
            )

        # Determine calculator type based on role
        calculator_type = "Marketing" if role == "Marketing" else "Developer"

        return LoginResponse(
            status="success",
            message="Login successful",
            role=role,
            calculator_type=calculator_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in login endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    finally:
        if client:
            client.close()

if __name__ == '__main__':
    import uvicorn
    logging.info(f"Starting server on {CONFIG.API_HOST}:{CONFIG.API_PORT}")
    uvicorn.run(
        "server:app",  # Import string instead of app object for reload support
        host=CONFIG.API_HOST,
        port=CONFIG.API_PORT,
        reload=CONFIG.API_DEBUG
    )
