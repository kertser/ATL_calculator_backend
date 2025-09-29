"""
Test script for the UV System Calculator API server
Tests all endpoints with various scenarios including success and error cases
"""

import requests
import json
import time
import logging
from config import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class APITester:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or f"http://{CONFIG.API_HOST}:{CONFIG.API_PORT}"
        self.session = requests.Session()
        self.test_results = []

    def run_test(self, test_name: str, test_func, expected_status: int = 200) -> bool:
        """Run a single test and record the result"""
        try:
            logging.info(f"Running test: {test_name}")

            start_time = time.time()
            response = test_func()
            duration = time.time() - start_time

            success = response.status_code == expected_status

            result = {
                "test_name": test_name,
                "success": success,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "duration_ms": round(duration * 1000, 2),
                "response_data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }

            self.test_results.append(result)

            if success:
                logging.info(f"✅ {test_name} - PASSED ({duration:.3f}s)")
            else:
                logging.error(f"❌ {test_name} - FAILED (Expected {expected_status}, got {response.status_code})")
                logging.error(f"Response: {result['response_data']}")

            return success

        except Exception as e:
            logging.error(f"❌ {test_name} - ERROR: {str(e)}")
            self.test_results.append({
                "test_name": test_name,
                "success": False,
                "error": str(e),
                "duration_ms": 0
            })
            return False

    def test_health_check(self):
        """Test the health check endpoint"""
        return self.session.get(f"{self.base_url}/health")

    def test_calculate_valid_request(self):
        """Test calculation with valid parameters"""
        payload = {
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
            "Flow Units": "m3/h",
            "D-1Log": 18.0
        }
        return self.session.post(
            f"{self.base_url}/calculate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

    def test_calculate_minimal_request(self):
        """Test calculation with minimal required parameters"""
        payload = {
            "Application": "Full Range",
            "Module": "RZ-104",
            "Model": "12",
            "Branch": "2",
            "Position": "Horizontal",
            "Lamp Type": "OzoneFree",
            "Efficiency": 100.0,
            "Relative Drive": 100.0,
            "UVT-1cm@254nm": 90.0,
            "Flow Rate": 50.0,
            "Flow Units": "US GPM"
        }
        return self.session.post(
            f"{self.base_url}/calculate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

    def test_calculate_with_optional_params(self):
        """Test calculation with all optional parameters"""
        payload = {
            "Application": "Dechlorination",
            "Module": "RZ-104",
            "Model": "12",
            "Branch": "1",
            "Position": "Vertical",
            "Lamp Type": "VUV",
            "Efficiency": 85.0,
            "Relative Drive": 95.0,
            "UVT-1cm@254nm": 95.0,
            "UVT-1cm@215nm": 95.0,
            "Flow Rate": 200.0,
            "Flow Units": "m3/h",
            "D-1Log": 18.0,
            "Pathogen": "Cryptosporidium"
        }
        return self.session.post(
            f"{self.base_url}/calculate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

    def test_calculate_missing_fields(self):
        """Test calculation with missing required fields"""
        payload = {
            "Application": "Municipal",
            "Module": "RZ-104",
            # Missing required fields intentionally
            "Efficiency": 80.0,
            "Flow Rate": 100.0
        }
        return self.session.post(
            f"{self.base_url}/calculate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

    def test_calculate_invalid_application(self):
        """Test calculation with invalid application type"""
        payload = {
            "Application": "InvalidType",
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
        return self.session.post(
            f"{self.base_url}/calculate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

    def test_calculate_out_of_range_values(self):
        """Test calculation with out-of-range values"""
        payload = {
            "Application": "Municipal",
            "Module": "RZ-104",
            "Model": "11",
            "Branch": "1",
            "Position": "Vertical",
            "Lamp Type": "Regular",
            "Efficiency": 150.0,  # Invalid: > 100
            "Relative Drive": -10.0,  # Invalid: < 0
            "UVT-1cm@254nm": 105.0,  # Invalid: > 100
            "Flow Rate": -50.0,  # Invalid: < 0
            "Flow Units": "m3/h"
        }
        return self.session.post(
            f"{self.base_url}/calculate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

    def test_calculate_invalid_json(self):
        """Test calculation with invalid JSON"""
        return self.session.post(
            f"{self.base_url}/calculate",
            data="invalid json content",
            headers={"Content-Type": "application/json"}
        )

    def test_calculate_empty_request(self):
        """Test calculation with empty request body"""
        return self.session.post(
            f"{self.base_url}/calculate",
            headers={"Content-Type": "application/json"}
        )

    def test_parameter_ranges_valid_system(self):
        """Test parameter ranges for a valid system"""
        return self.session.get(f"{self.base_url}/system/RZ-104-11/ranges")

    def test_parameter_ranges_invalid_system(self):
        """Test parameter ranges for an invalid system"""
        return self.session.get(f"{self.base_url}/system/INVALID-SYSTEM/ranges")

    def test_parameter_ranges_different_systems(self):
        """Test parameter ranges for different system types"""
        return self.session.get(f"{self.base_url}/system/RZ-104-12/ranges")

    def test_invalid_endpoint(self):
        """Test accessing an invalid endpoint"""
        return self.session.get(f"{self.base_url}/nonexistent")

    def test_wrong_http_method(self):
        """Test using wrong HTTP method for calculate endpoint"""
        return self.session.get(f"{self.base_url}/calculate")

    def run_all_tests(self):
        """Run all test cases"""
        logging.info("=" * 80)
        logging.info("Starting UV System Calculator API Tests")
        logging.info("=" * 80)

        # Test server availability
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                logging.error("❌ Server is not responding properly. Make sure the server is running.")
                return
        except requests.exceptions.ConnectionError:
            logging.error("❌ Cannot connect to server. Make sure it's running at " + self.base_url)
            return
        except Exception as e:
            logging.error(f"❌ Error connecting to server: {e}")
            return

        # Health check tests
        self.run_test("Health Check", self.test_health_check, 200)

        # Valid calculation tests
        self.run_test("Calculate - Valid Request", self.test_calculate_valid_request, 200)
        self.run_test("Calculate - Minimal Request", self.test_calculate_minimal_request, 200)
        self.run_test("Calculate - With Optional Parameters", self.test_calculate_with_optional_params, 200)

        # Error case tests
        self.run_test("Calculate - Missing Fields", self.test_calculate_missing_fields, 422)
        self.run_test("Calculate - Invalid Application", self.test_calculate_invalid_application, 422)
        self.run_test("Calculate - Out of Range Values", self.test_calculate_out_of_range_values, 422)
        self.run_test("Calculate - Invalid JSON", self.test_calculate_invalid_json, 422)
        self.run_test("Calculate - Empty Request", self.test_calculate_empty_request, 422)

        # Parameter ranges tests
        self.run_test("Parameter Ranges - Valid System", self.test_parameter_ranges_valid_system, 200)
        self.run_test("Parameter Ranges - Invalid System", self.test_parameter_ranges_invalid_system, 404)
        self.run_test("Parameter Ranges - Different System", self.test_parameter_ranges_different_systems, 200)

        # Invalid endpoint tests
        self.run_test("Invalid Endpoint", self.test_invalid_endpoint, 404)
        self.run_test("Wrong HTTP Method", self.test_wrong_http_method, 405)

        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        logging.info("=" * 80)
        logging.info("Test Summary")
        logging.info("=" * 80)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.get('success', False))
        failed_tests = total_tests - passed_tests

        logging.info(f"Total Tests: {total_tests}")
        logging.info(f"Passed: {passed_tests}")
        logging.info(f"Failed: {failed_tests}")
        logging.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")

        if failed_tests > 0:
            logging.info("\nFailed Tests:")
            for result in self.test_results:
                if not result.get('success', False):
                    logging.info(f"  - {result['test_name']}")
                    if 'error' in result:
                        logging.info(f"    Error: {result['error']}")
                    elif 'status_code' in result:
                        logging.info(f"    Status: {result['status_code']} (Expected: {result['expected_status']})")

        # Calculate average response time for successful tests
        successful_tests = [r for r in self.test_results if r.get('success', False) and 'duration_ms' in r]
        if successful_tests:
            avg_response_time = sum(r['duration_ms'] for r in successful_tests) / len(successful_tests)
            logging.info(f"\nAverage Response Time: {avg_response_time:.2f}ms")

    def save_detailed_results(self, filename: str = "test_results.json"):
        """Save detailed test results to a JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "base_url": self.base_url,
                    "summary": {
                        "total_tests": len(self.test_results),
                        "passed": sum(1 for r in self.test_results if r.get('success', False)),
                        "failed": sum(1 for r in self.test_results if not r.get('success', False))
                    },
                    "results": self.test_results
                }, f, indent=2)
            logging.info(f"Detailed results saved to {filename}")
        except Exception as e:
            logging.error(f"Failed to save results: {e}")


def main():
    """Main function to run the tests"""
    import argparse

    parser = argparse.ArgumentParser(description="Test the UV System Calculator API")
    parser.add_argument("--host", default=CONFIG.API_HOST, help="API host")
    parser.add_argument("--port", default=CONFIG.API_PORT, type=int, help="API port")
    parser.add_argument("--save-results", action="store_true", help="Save detailed results to JSON")

    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    tester = APITester(base_url)

    tester.run_all_tests()

    if args.save_results:
        tester.save_detailed_results()


if __name__ == "__main__":
    main()
