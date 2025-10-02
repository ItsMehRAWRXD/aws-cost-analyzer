#!/usr/bin/env python3
"""
Test script to verify registration functionality
"""

import requests
import json

# Test registration
def test_registration():
    url = "http://localhost:5000/register"
    
    # Test data
    test_data = {
        'email': 'test@example.com',
        'password': 'testpassword123'
    }
    
    print("Testing registration...")
    print(f"URL: {url}")
    print(f"Data: {test_data}")
    
    try:
        # Test GET request (should show registration form)
        response = requests.get(url)
        print(f"GET Response Status: {response.status_code}")
        print(f"GET Response contains 'Create Account': {'Create Account' in response.text}")
        
        # Test POST request (should register user)
        response = requests.post(url, data=test_data)
        print(f"POST Response Status: {response.status_code}")
        print(f"POST Response URL: {response.url}")
        
        if response.status_code == 302:  # Redirect
            print("SUCCESS: Registration successful - redirected to login")
        else:
            print(f"FAILED: Registration failed - Status: {response.status_code}")
            print(f"Response text: {response.text[:500]}...")
            
    except Exception as e:
        print(f"ERROR: Error testing registration: {e}")

def test_login():
    url = "http://localhost:5000/login"
    
    # Test data
    test_data = {
        'email': 'test@example.com',
        'password': 'testpassword123'
    }
    
    print("\nTesting login...")
    print(f"URL: {url}")
    print(f"Data: {test_data}")
    
    try:
        # Test POST request (should login user)
        response = requests.post(url, data=test_data)
        print(f"POST Response Status: {response.status_code}")
        print(f"POST Response URL: {response.url}")
        
        if response.status_code == 302:  # Redirect
            print("SUCCESS: Login successful - redirected to dashboard")
        else:
            print(f"FAILED: Login failed - Status: {response.status_code}")
            print(f"Response text: {response.text[:500]}...")
            
    except Exception as e:
        print(f"ERROR: Error testing login: {e}")

if __name__ == "__main__":
    print("Testing AWS Cost Analyzer Registration & Login")
    print("=" * 50)
    
    test_registration()
    test_login()
    
    print("\n" + "=" * 50)
    print("Test completed!")
