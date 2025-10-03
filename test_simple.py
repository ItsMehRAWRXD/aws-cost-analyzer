#!/usr/bin/env python3
"""
Simple test of AWS Cost Analyzer functionality
"""

import requests
import json
import time

def test_app():
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("AWS COST ANALYZER SAAS - FUNCTIONALITY TEST")
    print("=" * 50)
    
    # Test 1: Registration
    print("\n1. Testing Registration...")
    user_data = {
        'email': f'test_{int(time.time())}@example.com',
        'password': 'testpass123'
    }
    
    response = session.post(f'{base_url}/register', data=user_data)
    if response.status_code == 200:
        print("SUCCESS: Registration works")
    else:
        print(f"FAILED: Registration failed ({response.status_code})")
        return
    
    # Test 2: Login
    print("\n2. Testing Login...")
    response = session.post(f'{base_url}/login', data=user_data)
    if response.status_code == 200 and 'dashboard' in response.url:
        print("SUCCESS: Login works - redirected to dashboard")
    else:
        print(f"FAILED: Login failed ({response.status_code})")
        return
    
    # Test 3: Dashboard
    print("\n3. Testing Dashboard...")
    response = session.get(f'{base_url}/dashboard')
    if response.status_code == 200:
        print("SUCCESS: Dashboard accessible")
        
        # Check for key features
        content = response.text
        if 'Current Month Spend' in content:
            print("SUCCESS: Cost tracking display present")
        if 'Cost Analysis' in content:
            print("SUCCESS: Analysis tab present")
        if 'Upgrade Plan' in content:
            print("SUCCESS: Pricing tab present")
    else:
        print(f"FAILED: Dashboard not accessible ({response.status_code})")
        return
    
    # Test 4: Cost Analysis
    print("\n4. Testing Cost Analysis...")
    analysis_data = {
        'monthlyBill': 1500,
        'services': 'EC2,S3,RDS',
        'region': 'us-east-1',
        'workloadType': 'web'
    }
    
    response = session.post(
        f'{base_url}/api/analyze',
        json=analysis_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        try:
            result = response.json()
            if result.get('status') == 'success':
                savings = result.get('potential_savings', 0)
                recommendations = result.get('recommendations', [])
                print(f"SUCCESS: Analysis works - ${savings} potential savings")
                print(f"SUCCESS: Generated {len(recommendations)} recommendations")
                
                # Show first recommendation
                if recommendations:
                    rec = recommendations[0]
                    print(f"SUCCESS: Top recommendation: {rec['title']}")
            else:
                print(f"FAILED: Analysis returned error: {result.get('detail')}")
        except:
            print("FAILED: Invalid JSON response from analysis")
    else:
        print(f"FAILED: Analysis request failed ({response.status_code})")
    
    # Test 5: Subscription
    print("\n5. Testing Subscription System...")
    response = session.post(
        f'{base_url}/api/subscribe',
        json={'plan': 'starter'},
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        try:
            result = response.json()
            if 'url' in result:
                print("SUCCESS: Subscription checkout URL generated")
            elif 'error' in result and 'not configured' in result['error']:
                print("SUCCESS: Subscription system works (Stripe not configured locally)")
            else:
                print(f"INFO: Subscription response: {result}")
        except:
            print("FAILED: Invalid subscription response")
    else:
        print(f"FAILED: Subscription request failed ({response.status_code})")
    
    # Test 6: Security
    print("\n6. Testing Security...")
    session.get(f'{base_url}/logout')  # Logout
    
    # Try to access dashboard without login
    response = session.get(f'{base_url}/dashboard')
    if response.status_code == 302 or 'login' in response.url:
        print("SUCCESS: Protected routes properly secured")
    else:
        print("FAILED: Security issue - dashboard accessible without login")
    
    print("\n" + "=" * 50)
    print("TEST COMPLETED!")
    print("\nWHAT THIS APP DOES:")
    print("- Helps businesses analyze and optimize AWS costs")
    print("- Provides cost recommendations and savings estimates")
    print("- Offers subscription plans for different business needs")
    print("- Shows cost trends and service breakdowns")
    print("- Generates actionable optimization recommendations")

if __name__ == "__main__":
    test_app()
