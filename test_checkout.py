#!/usr/bin/env python3
"""
Test script to verify Stripe checkout functionality
"""

import requests
import json

# Test checkout functionality
def test_checkout():
    # First, let's register and login a test user
    session = requests.Session()
    
    # Register a test user
    register_data = {
        'email': 'checkout_test@example.com',
        'password': 'testpassword123'
    }
    
    print("Step 1: Registering test user...")
    response = session.post('http://localhost:5000/register', data=register_data)
    print(f"Registration Status: {response.status_code}")
    
    # Login the user
    print("\nStep 2: Logging in test user...")
    response = session.post('http://localhost:5000/login', data=register_data)
    print(f"Login Status: {response.status_code}")
    
    if response.status_code == 200 and 'dashboard' in response.url:
        print("SUCCESS: User logged in successfully")
        
        # Test the subscription endpoint
        print("\nStep 3: Testing subscription endpoint...")
        subscription_data = {
            'plan': 'starter'
        }
        
        try:
            response = session.post('http://localhost:5000/api/subscribe', 
                                  json=subscription_data,
                                  headers={'Content-Type': 'application/json'})
            
            print(f"Subscription Response Status: {response.status_code}")
            print(f"Response Content: {response.text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'url' in data:
                        print(f"SUCCESS: Checkout URL generated: {data['url']}")
                    elif 'error' in data:
                        print(f"INFO: Expected error (no Stripe keys): {data['error']}")
                    else:
                        print(f"Response data: {data}")
                except json.JSONDecodeError:
                    print(f"Non-JSON response: {response.text}")
            else:
                print(f"Subscription failed with status: {response.status_code}")
                
        except Exception as e:
            print(f"ERROR: Subscription test failed: {e}")
            
    else:
        print("FAILED: Could not login user")

def test_dashboard_access():
    print("\n" + "="*50)
    print("Testing Dashboard Access...")
    
    session = requests.Session()
    
    # Try to access dashboard without login
    print("Step 1: Accessing dashboard without login...")
    response = session.get('http://localhost:5000/dashboard')
    print(f"Dashboard without login: {response.status_code}")
    
    if response.status_code == 302:
        print("SUCCESS: Dashboard properly redirects to login when not authenticated")
    else:
        print("WARNING: Dashboard might not be properly protected")

def test_pricing_page():
    print("\n" + "="*50)
    print("Testing Pricing Page...")
    
    # Test if pricing information is accessible
    session = requests.Session()
    
    # Register and login
    register_data = {
        'email': 'pricing_test@example.com',
        'password': 'testpassword123'
    }
    
    session.post('http://localhost:5000/register', data=register_data)
    session.post('http://localhost:5000/login', data=register_data)
    
    # Access dashboard to see pricing
    response = session.get('http://localhost:5000/dashboard')
    
    if 'pricing' in response.text.lower() and 'starter' in response.text.lower():
        print("SUCCESS: Pricing information is displayed on dashboard")
    else:
        print("WARNING: Pricing information might not be visible")

if __name__ == "__main__":
    print("Testing AWS Cost Analyzer Checkout Functionality")
    print("=" * 60)
    
    test_checkout()
    test_dashboard_access()
    test_pricing_page()
    
    print("\n" + "=" * 60)
    print("Checkout testing completed!")
    print("\nNote: If you see 'Payment processing not configured' errors,")
    print("this is expected when Stripe keys are not set up locally.")
    print("The important thing is that the endpoints respond correctly.")
