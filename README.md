# UV System Calculator API

A FastAPI-based REST API server for UV system calculations including Reduction Equivalent Dose (RED), head loss, and power consumption calculations.

## Quick Start

### Prerequisites
- Python 3.8+
- UV package manager

### Installation & Running

1. **Using UV (recommended):**
   ```bash
   uv sync
   uv run python server.py
   ```

The server will start on `http://localhost:5000` by default.

## API Endpoints

### 1. Health Check
**GET** `/health`

Check if the server and calculator are running properly.

**Response:**
```json
{
  "status": "healthy",
  "calculator_initialized": true
}
```

### 2. Calculate UV System Parameters
**POST** `/calculate`

Main calculation endpoint that returns RED and other system parameters.

**Request Body:**
```json
{
  "Application": "Municipal",
  "Module": "RZ-104",
  "Model": "11",
  "Branch": "1",
  "Position": "Vertical",
  "Lamp Type": "Regular",
  "Efficiency": 80.0,
  "Relative Drive": 90.0,
  "UVT-1cm@254nm": 85.0,
  "UVT-1cm@215nm": 85.0,
  "Flow Rate": 100.0,
  "Flow Units": "m3/h",
  "D-1Log": 18.0,
  "Pathogen": "Cryptosporidium"
}
```

**Required Fields:**
- `Application`: Application type
- `Module`: Module identifier (e.g., "RZ-104")
- `Model`: Model identifier (e.g., "11", "12")
- `Branch`: Branch identifier
- `Position`: Position type
- `Lamp Type`: Lamp type
- `Efficiency`: Efficiency percentage (0-100)
- `Relative Drive`: Relative drive percentage (0-100)
- `UVT-1cm@254nm`: UVT at 254nm (0-100)
- `Flow Rate`: Flow rate (must be > 0)
- `Flow Units`: Flow rate units

**Optional Fields:**
- `UVT-1cm@215nm`: UVT at 215nm (0-100)
- `D-1Log`: D-1Log value
- `Pathogen`: Pathogen type

**Success Response (200):** (example)
```json
{
  "Reduction Equivalent Dose": 42.5,
  "Head Loss": "TBD",
  "Maximum Electrical Power": "TBD",
  "Average Lamp Power Consumption": "TBD",
  "Expected LI": "TBD",
  "status": "success",
  "calculation_details": {
    "system_type": "RZ-104-11",
    "number_of_lamps": 12,
    "lamp_power_watts": 320.0,
    "parameters": {
      "flow": 100.0,
      "uvt": 85.0,
      "uvt215": 85.0,
      "d1_log": 18.0
    },
    "lamp_settings": {
      "power": [90.0, 90.0, 90.0, 90.0, 90.0, 90.0, 90.0, 90.0, 90.0, 90.0, 90.0, 90.0],
      "efficiency": [80.0, 80.0, 80.0, 80.0, 80.0, 80.0, 80.0, 80.0, 80.0, 80.0, 80.0, 80.0]
    }
  }
}
```

**Error Response (400/422):**
```json
{
  "detail": "Validation error message"
}
```

### 3. Get Parameter Ranges
**GET** `/system/{system_type}/ranges`

Get valid parameter ranges for a specific UV system.

**Example:** `GET /system/RZ-104-11/ranges`

**Response:**
```json
{
  "system_type": "RZ-104-11",
  "ranges": {
    "flow": {
      "min": 10.0,
      "max": 500.0,
      "unit": "m3/h"
    },
    "uvt": {
      "min": 70.0,
      "max": 98.0,
      "unit": "%"
    }
  },
  "status": "success"
}
```

### 4. Get Supported Systems
**GET** `/systems/supported`

Get list of all supported UV systems grouped by series.

**Response:**
```json
{
  "systems": {
    "RZ Series": [
      "RZ-104-11",
      "RZ-104-12",
      "RZ-163-11",
      "RZ-163-12"
    ],
    "RZM Series": [
      "RZM-163-11",
      "RZM-163-12"
    ],
    "RZMW Series": [
      "RZMW-163-11",
      "RZMW-163-12"
    ]
  },
  "status": "success"
}
```

## Valid Values

### Application Types
- `"Full Range"`
- `"Municipal"`
- `"Dechlorination"`

### Position Types
- `"Vertical"`
- `"Horizontal"`

### Lamp Types
- `"Regular"`
- `"OzoneFree"`
- `"VUV"`

### Flow Units
- `"m3/h"`
- `"US GPM"`

### System Types
System type is automatically generated from Module + Model:
- Module: `"RZ-104"`, `"RZM-163"`, etc.
- Model: `"11"`, `"12"`, etc.
- Result: `"RZ-104-11"`, `"RZM-163-12"`, etc.

## Frontend Integration Examples

### JavaScript/Fetch
```javascript
// Health check
async function checkHealth() {
  const response = await fetch('http://localhost:5000/health');
  const data = await response.json();
  console.log('Server status:', data.status);
}

// Calculate RED
async function calculateRED(params) {
  const response = await fetch('http://localhost:5000/calculate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}

// Get parameter ranges
async function getParameterRanges(systemType) {
  const response = await fetch(`http://localhost:5000/system/${systemType}/ranges`);
  return await response.json();
}

// Get supported systems
async function getSupportedSystems() {
  const response = await fetch('http://localhost:5000/systems/supported');
  return await response.json();
}

// Example usage
const calculationParams = {
  "Application": "Municipal",
  "Module": "RZ-104",
  "Model": "11",
  "Branch": "1",
  "Position": "Vertical",
  "Lamp Type": "Regular",
  "Efficiency": 80.0,
  "Relative Drive": 90.0,
  "UVT-1cm@254nm": 85.0,
  "Flow Rate": 100.0,
  "Flow Units": "m3/h"
};

calculateRED(calculationParams)
  .then(result => console.log('RED:', result['Reduction Equivalent Dose']))
  .catch(error => console.error('Error:', error.message));
```

### React Hook Example
```javascript
import { useState, useEffect } from 'react';

function useUVCalculator() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const calculate = async (params) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:5000/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail);
      }
      
      const result = await response.json();
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  
  return { calculate, isLoading, error };
}
```

### Python/Requests Example
```python
import requests

# Health check
response = requests.get('http://localhost:5000/health')
print(f"Server status: {response.json()['status']}")

# Calculate RED
params = {
    "Application": "Municipal",
    "Module": "RZ-104",
    "Model": "11",
    "Branch": "1",
    "Position": "Vertical",
    "Lamp Type": "Regular",
    "Efficiency": 80.0,
    "Relative Drive": 90.0,
    "UVT-1cm@254nm": 85.0,
    "Flow Rate": 100.0,
    "Flow Units": "m3/h"
}

response = requests.post('http://localhost:5000/calculate', json=params)
if response.status_code == 200:
    result = response.json()
    print(f"RED: {result['Reduction Equivalent Dose']}")
else:
    print(f"Error: {response.json()}")
```

## Error Handling

The API returns standard HTTP status codes:

- **200**: Success
- **400**: Bad Request (calculation error)
- **404**: Not Found (invalid system type)
- **422**: Validation Error (invalid input parameters)
- **500**: Internal Server Error

### Common Error Scenarios

1. **Missing Required Fields**
   ```json
   {
     "detail": [
       {
         "type": "missing",
         "loc": ["body", "Module"],
         "msg": "Field required"
       }
     ]
   }
   ```

2. **Invalid Value Range**
   ```json
   {
     "detail": [
       {
         "type": "greater_than",
         "loc": ["body", "Flow Rate"],
         "msg": "Input should be greater than 0"
       }
     ]
   }
   ```

3. **Invalid Application Type**
   ```json
   {
     "detail": [
       {
         "type": "value_error",
         "loc": ["body", "Application"],
         "msg": "Application must be one of: Full Range, Municipal, Dechlorination"
       }
     ]
   }
   ```

4. **System Not Found**
   ```json
   {
     "detail": "System type 'INVALID-SYSTEM' not found"
   }
   ```

## Testing

Use the provided test script to verify API functionality:

```bash
# Run all tests
uv run python test_server.py

# Run tests with custom host/port
uv run python test_server.py --host localhost --port 5000

# Save detailed results
uv run python test_server.py --save-results
```

## Configuration

Default configuration is in `config.py`:

- **Host**: `localhost`
- **Port**: `5000`
- **Debug Mode**: `True`

## CORS

The API includes CORS middleware configured to allow all origins. For production, update the `allow_origins` parameter in `server.py` to restrict access to specific domains.

## Postman Collection

You can test the API using Postman by importing the following endpoints:

1. **Health Check**: `GET http://localhost:5000/health`
2. **Calculate**: `POST http://localhost:5000/calculate`
3. **Parameter Ranges**: `GET http://localhost:5000/system/RZ-104-11/ranges`

## Support

For issues or questions:
1. Check the server logs for detailed error messages
2. Verify all required fields are included in requests
3. Ensure parameter values are within valid ranges
4. Use the health check endpoint to verify server status

## Notes

- Currently, only RED calculation is implemented
- Head Loss, Maximum Electrical Power, Average Lamp Power Consumption, and Expected LI return "TBD"
- The system type is formed by combining Module and Model with a hyphen (e.g., "RZ-104" + "11" = "RZ-104-11")
- UVT values should be percentages (0-100)
- Flow rate must be positive
- Efficiency and Relative Drive values should be percentages (0-100)
