"""
Test script for pressure drop calculation
"""
import pytest
from calculator import REDLibrary


def test_pressure_drop_calculation():
    """Test pressure drop calculation for a sample system"""
    calculator = REDLibrary()

    # Test with RZ-104-11 system at 100 m³/h
    result = calculator.calculate_pressure_drop(
        system_type="RZ-104-11",
        flow=100.0
    )

    print(f"\nPressure Drop Result: {result}")

    assert result is not None
    assert result["status"] == "success"
    assert "result" in result
    assert "unit" in result
    assert result["unit"] == "[cmH2O]"
    assert result["result"] > 0  # Pressure drop should be positive

    # Verify the calculation: dP = Cflow_1 * flow^2 + Cflow_2 * flow
    # For RZ-104-11: Cflow_1 = 2.22E-4, Cflow_2 = 0
    expected = 2.22e-4 * (100.0 ** 2) + 0 * 100.0
    assert abs(result["result"] - round(expected, 2)) < 0.01


def test_pressure_drop_invalid_system():
    """Test pressure drop with invalid system type"""
    calculator = REDLibrary()

    result = calculator.calculate_pressure_drop(
        system_type="INVALID-SYSTEM",
        flow=100.0
    )

    print(f"\nInvalid System Result: {result}")

    assert result is not None
    assert result["status"] == "error"
    assert "error" in result


def test_pressure_drop_zero_flow():
    """Test pressure drop with zero flow rate"""
    calculator = REDLibrary()

    result = calculator.calculate_pressure_drop(
        system_type="RZ-104-11",
        flow=0.0
    )

    print(f"\nZero Flow Result: {result}")

    assert result is not None
    assert result["status"] == "error"
    assert "error" in result


def test_pressure_drop_different_flows():
    """Test pressure drop calculation at different flow rates"""
    calculator = REDLibrary()

    flows = [50, 100, 200, 500]

    for flow in flows:
        result = calculator.calculate_pressure_drop(
            system_type="RZ-104-11",
            flow=flow
        )

        print(f"\nFlow: {flow} m³/h, Pressure Drop: {result['result']} {result['unit']}")

        assert result is not None
        assert result["status"] == "success"
        assert result["result"] > 0


if __name__ == "__main__":
    # Run tests manually
    print("=" * 60)
    print("Testing Pressure Drop Calculations")
    print("=" * 60)

    try:
        test_pressure_drop_calculation()
        print("\n✓ Test 1: Basic pressure drop calculation - PASSED")
    except AssertionError as e:
        print(f"\n✗ Test 1: Basic pressure drop calculation - FAILED: {e}")

    try:
        test_pressure_drop_invalid_system()
        print("✓ Test 2: Invalid system type - PASSED")
    except AssertionError as e:
        print(f"✗ Test 2: Invalid system type - FAILED: {e}")

    try:
        test_pressure_drop_zero_flow()
        print("✓ Test 3: Zero flow rate - PASSED")
    except AssertionError as e:
        print(f"✗ Test 3: Zero flow rate - FAILED: {e}")

    try:
        test_pressure_drop_different_flows()
        print("✓ Test 4: Different flow rates - PASSED")
    except AssertionError as e:
        print(f"✗ Test 4: Different flow rates - FAILED: {e}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)

