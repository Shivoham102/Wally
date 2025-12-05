"""Simple test script for Wally API endpoints."""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")


def test_text_command(command: str):
    """Test text command endpoint."""
    print(f"Testing text command: '{command}'")
    response = requests.post(
        f"{BASE_URL}/api/v1/voice/text-command",
        json={"command": command}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def test_order_history():
    """Test order history endpoint."""
    print("Testing order history endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/orders/history")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def test_automation_status():
    """Test automation status endpoint."""
    print("Testing automation status endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/automation/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


if __name__ == "__main__":
    print("=" * 50)
    print("Wally API Test Script")
    print("=" * 50)
    print()
    
    # Test health
    try:
        test_health()
    except Exception as e:
        print(f"Health check failed: {e}\n")
        print("Make sure the server is running: uvicorn app.main:app --reload")
        exit(1)
    
    # Test text commands
    test_commands = [
        "Add milk, eggs, and bread",
        "Add my usual groceries",
        "Show my previous orders"
    ]
    
    for cmd in test_commands:
        try:
            test_text_command(cmd)
        except Exception as e:
            print(f"Command test failed: {e}\n")
    
    # Test order history
    try:
        test_order_history()
    except Exception as e:
        print(f"Order history test failed: {e}\n")
    
    # Test automation status
    try:
        test_automation_status()
    except Exception as e:
        print(f"Automation status test failed: {e}\n")
    
    print("=" * 50)
    print("Tests completed!")
    print("=" * 50)



