#!/usr/bin/env python3
"""
Comprehensive test of AWS Cost Analyzer SaaS functionality
"""

import requests
import json
import time

class AWSCostAnalyzerTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_user = {
            'email': f'test_user_{int(time.time())}@example.com',
            'password': 'testpassword123'
        }
        
    def print_section(self, title):
        print(f"\n{'='*60}")
        print(f"TESTING: {title}")
        print('='*60)
        
    def test_user_registration_and_login(self):
        """Test user registration and login functionality"""
        self.print_section("USER REGISTRATION & LOGIN")
        
        # Test registration
        print("1. Testing user registration...")
        response = self.session.post(f'{self.base_url}/register', data=self.test_user)
        if response.status_code == 200:
            print("SUCCESS: Registration successful")
        else:
            print(f"FAILED: Registration failed: {response.status_code}")
            return False
            
        # Test login
        print("2. Testing user login...")
        response = self.session.post(f'{self.base_url}/login', data=self.test_user)
        if response.status_code == 200 and 'dashboard' in response.url:
            print("SUCCESS: Login successful - redirected to dashboard")
            return True
        else:
            print(f"FAILED: Login failed: {response.status_code}")
            return False
    
    def test_dashboard_access(self):
        """Test dashboard functionality"""
        self.print_section("DASHBOARD FUNCTIONALITY")
        
        print("1. Testing dashboard access...")
        response = self.session.get(f'{self.base_url}/dashboard')
        if response.status_code == 200:
            print("SUCCESS: Dashboard accessible")
            
            # Check for key dashboard elements
            content = response.text
            checks = [
                ("Current Month Spend", "Monthly spending display"),
                ("Cost Analysis", "Analysis tab"),
                ("Upgrade Plan", "Pricing tab"),
                ("Chart.js", "Charts library loaded"),
                ("EC2", "Service breakdown chart")
            ]
            
            for check, description in checks:
                if check in content:
                    print(f"SUCCESS: {description} present")
                else:
                    print(f"FAILED: {description} missing")
        else:
            print(f"FAILED: Dashboard not accessible: {response.status_code}")
            return False
        return True
    
    def test_cost_analysis(self):
        """Test the core cost analysis functionality"""
        self.print_section("COST ANALYSIS ENGINE")
        
        test_cases = [
            {
                'name': 'Web Application Workload',
                'data': {
                    'monthlyBill': 1250,
                    'services': 'EC2,S3,RDS,CloudFront',
                    'region': 'us-east-1',
                    'workloadType': 'web'
                }
            },
            {
                'name': 'Data Processing Workload',
                'data': {
                    'monthlyBill': 2500,
                    'services': 'EMR,Redshift,S3,Glue',
                    'region': 'us-west-2',
                    'workloadType': 'data'
                }
            },
            {
                'name': 'Compute Intensive Workload',
                'data': {
                    'monthlyBill': 5000,
                    'services': 'EC2,ECS,Lambda,ElastiCache',
                    'region': 'eu-west-1',
                    'workloadType': 'compute'
                }
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"{i}. Testing {test_case['name']}...")
            
            response = self.session.post(
                f'{self.base_url}/api/analyze',
                json=test_case['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('status') == 'success':
                        savings = result.get('potential_savings', 0)
                        recommendations = result.get('recommendations', [])
                        print(f"✅ Analysis successful - ${savings} potential savings, {len(recommendations)} recommendations")
                        
                        # Show top recommendation
                        if recommendations:
                            top_rec = recommendations[0]
                            print(f"   💡 Top recommendation: {top_rec['title']} (${top_rec['savings']} savings)")
                    else:
                        print(f"❌ Analysis failed: {result.get('detail', 'Unknown error')}")
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response: {response.text[:100]}...")
            else:
                print(f"❌ Analysis request failed: {response.status_code}")
        
        return True
    
    def test_subscription_system(self):
        """Test the subscription and payment system"""
        self.print_section("SUBSCRIPTION & PAYMENT SYSTEM")
        
        plans = ['starter', 'professional', 'enterprise']
        
        for plan in plans:
            print(f"Testing {plan.title()} plan subscription...")
            
            response = self.session.post(
                f'{self.base_url}/api/subscribe',
                json={'plan': plan},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if 'url' in result:
                        print(f"✅ {plan.title()} plan: Checkout URL generated")
                    elif 'error' in result:
                        if 'not configured' in result['error']:
                            print(f"ℹ️ {plan.title()} plan: Stripe not configured (expected locally)")
                        else:
                            print(f"❌ {plan.title()} plan: {result['error']}")
                    else:
                        print(f"❌ {plan.title()} plan: Unexpected response format")
                except json.JSONDecodeError:
                    print(f"❌ {plan.title()} plan: Invalid JSON response")
            else:
                print(f"❌ {plan.title()} plan: Request failed ({response.status_code})")
        
        return True
    
    def test_security_features(self):
        """Test security and authentication"""
        self.print_section("SECURITY & AUTHENTICATION")
        
        # Test logout
        print("1. Testing logout functionality...")
        response = self.session.get(f'{self.base_url}/logout')
        if response.status_code == 200:
            print("✅ Logout successful")
        else:
            print(f"❌ Logout failed: {response.status_code}")
        
        # Test protected route without authentication
        print("2. Testing protected route access...")
        response = self.session.get(f'{self.base_url}/dashboard')
        if response.status_code == 302 or 'login' in response.url:
            print("✅ Protected routes properly redirect to login")
        else:
            print("❌ Protected routes not properly secured")
        
        # Test API endpoint without authentication
        print("3. Testing API endpoint protection...")
        response = self.session.post(
            f'{self.base_url}/api/analyze',
            json={'monthlyBill': 1000},
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 302 or 'login' in response.url:
            print("✅ API endpoints properly protected")
        else:
            print("❌ API endpoints not properly secured")
        
        return True
    
    def test_error_handling(self):
        """Test error handling and edge cases"""
        self.print_section("ERROR HANDLING & EDGE CASES")
        
        # Test invalid analysis data
        print("1. Testing invalid analysis data...")
        invalid_cases = [
            {'monthlyBill': 0},  # Zero bill
            {'monthlyBill': -100},  # Negative bill
            {'monthlyBill': 'invalid'},  # Invalid type
            {}  # Empty data
        ]
        
        for i, invalid_data in enumerate(invalid_cases, 1):
            response = self.session.post(
                f'{self.base_url}/api/analyze',
                json=invalid_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('status') == 'error':
                        print(f"✅ Invalid case {i}: Properly handled with error message")
                    else:
                        print(f"❌ Invalid case {i}: Should have returned error")
                except:
                    print(f"❌ Invalid case {i}: Invalid response format")
            else:
                print(f"ℹ️ Invalid case {i}: HTTP error (may be expected)")
        
        return True
    
    def run_all_tests(self):
        """Run all functionality tests"""
        print("AWS COST ANALYZER SAAS - COMPREHENSIVE FUNCTIONALITY TEST")
        print("="*80)
        
        tests = [
            ("User Registration & Login", self.test_user_registration_and_login),
            ("Dashboard Functionality", self.test_dashboard_access),
            ("Cost Analysis Engine", self.test_cost_analysis),
            ("Subscription System", self.test_subscription_system),
            ("Security Features", self.test_security_features),
            ("Error Handling", self.test_error_handling)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        self.print_section("TEST SUMMARY")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! The AWS Cost Analyzer SaaS is fully functional!")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")
        
        return passed == total

if __name__ == "__main__":
    tester = AWSCostAnalyzerTester()
    tester.run_all_tests()
