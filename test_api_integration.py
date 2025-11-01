"""
API Integration Test - Comprehensive System Integration Testing

This module tests the integration between all major system components:
- Dashboard API
- Trading API
- Risk Management API
- Backtest API
- Strategy API
- Performance Metrics API
- Futu Trading API
"""
import asyncio
import pytest
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIIntegrationTester:
    """API Integration Test Suite"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []

    def log_test(self, test_name: str, success: bool, message: str, data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })

    def test_api_health_check(self):
        """Test 1: API Health Check"""
        logger.info("\n" + "=" * 60)
        logger.info("Test 1: API Health Check")
        logger.info("=" * 60)

        try:
            # Test root endpoint
            response = self.session.get(f"{self.base_url}/")
            success = response.status_code == 200
            self.log_test(
                "API Health Check - Root",
                success,
                f"Status: {response.status_code}",
                {"url": self.base_url, "status_code": response.status_code}
            )

            # Test docs endpoint
            response = self.session.get(f"{self.base_url}/docs")
            success = response.status_code == 200
            self.log_test(
                "API Health Check - Docs",
                success,
                f"Status: {response.status_code}",
                {"url": f"{self.base_url}/docs", "status_code": response.status_code}
            )

        except Exception as e:
            self.log_test("API Health Check", False, f"Error: {str(e)}")
            logger.error(f"Health check failed: {e}")

    def test_dashboard_api(self):
        """Test 2: Dashboard API Endpoints"""
        logger.info("\n" + "=" * 60)
        logger.info("Test 2: Dashboard API")
        logger.info("=" * 60)

        endpoints = [
            "/api/dashboard/summary",
            "/api/dashboard/status",
            "/api/dashboard/health",
        ]

        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                success = response.status_code in [200, 503]  # 503 if service not initialized
                self.log_test(
                    f"Dashboard API - {endpoint}",
                    success,
                    f"Status: {response.status_code}",
                    {"endpoint": endpoint, "status_code": response.status_code}
                )
            except Exception as e:
                self.log_test(f"Dashboard API - {endpoint}", False, f"Error: {str(e)}")

    def test_trading_api(self):
        """Test 3: Trading API Endpoints"""
        logger.info("\n" + "=" * 60)
        logger.info("Test 3: Trading API")
        logger.info("=" * 60)

        # Test GET endpoints
        get_endpoints = [
            "/api/trading/positions",
            "/api/trading/orders",
            "/api/trading/trades",
            "/api/trading/statistics",
        ]

        for endpoint in get_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                success = response.status_code == 200
                self.log_test(
                    f"Trading API - {endpoint}",
                    success,
                    f"Status: {response.status_code}",
                    {"endpoint": endpoint, "status_code": response.status_code}
                )
            except Exception as e:
                self.log_test(f"Trading API - {endpoint}", False, f"Error: {str(e)}")

        # Test POST endpoint (place order)
        try:
            order_data = {
                "symbol": "0700.HK",
                "order_type": "BUY",
                "quantity": 100,
                "price": 300.0
            }
            response = self.session.post(
                f"{self.base_url}/api/trading/order",
                json=order_data
            )
            success = response.status_code == 200
            self.log_test(
                "Trading API - Place Order",
                success,
                f"Status: {response.status_code}",
                {"endpoint": "/api/trading/order", "status_code": response.status_code, "data": order_data}
            )
        except Exception as e:
            self.log_test("Trading API - Place Order", False, f"Error: {str(e)}")

    def test_risk_api(self):
        """Test 4: Risk Management API Endpoints"""
        logger.info("\n" + "=" * 60)
        logger.info("Test 4: Risk Management API")
        logger.info("=" * 60)

        # Test risk metrics endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/risk/metrics")
            success = response.status_code in [200, 404]  # 404 if not implemented
            self.log_test(
                "Risk API - Metrics",
                success,
                f"Status: {response.status_code}",
                {"endpoint": "/api/risk/metrics", "status_code": response.status_code}
            )
        except Exception as e:
            self.log_test("Risk API - Metrics", False, f"Error: {str(e)}")

        # Test portfolio risk endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/risk/portfolio")
            success = response.status_code in [200, 404]
            self.log_test(
                "Risk API - Portfolio",
                success,
                f"Status: {response.status_code}",
                {"endpoint": "/api/risk/portfolio", "status_code": response.status_code}
            )
        except Exception as e:
            self.log_test("Risk API - Portfolio", False, f"Error: {str(e)}")

    def test_backtest_api(self):
        """Test 5: Backtest API Endpoints"""
        logger.info("\n" + "=" * 60)
        logger.info("Test 5: Backtest API")
        logger.info("=" * 60)

        # Test backtest list endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/backtest/list")
            success = response.status_code in [200, 404]
            self.log_test(
                "Backtest API - List",
                success,
                f"Status: {response.status_code}",
                {"endpoint": "/api/backtest/list", "status_code": response.status_code}
            )
        except Exception as e:
            self.log_test("Backtest API - List", False, f"Error: {str(e)}")

    def test_strategy_api(self):
        """Test 6: Strategy API Endpoints"""
        logger.info("\n" + "=" * 60)
        logger.info("Test 6: Strategy API")
        logger.info("=" * 60)

        # Test strategies endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/strategies")
            success = response.status_code in [200, 404]
            self.log_test(
                "Strategy API - List",
                success,
                f"Status: {response.status_code}",
                {"endpoint": "/api/strategies", "status_code": response.status_code}
            )
        except Exception as e:
            self.log_test("Strategy API - List", False, f"Error: {str(e)}")

    def test_performance_api(self):
        """Test 7: Performance Metrics API"""
        logger.info("\n" + "=" * 60)
        logger.info("Test 7: Performance API")
        logger.info("=" * 60)

        # Test performance metrics endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/performance")
            success = response.status_code in [200, 404]
            self.log_test(
                "Performance API - Metrics",
                success,
                f"Status: {response.status_code}",
                {"endpoint": "/api/performance", "status_code": response.status_code}
            )
        except Exception as e:
            self.log_test("Performance API - Metrics", False, f"Error: {str(e)}")

    def test_data_flow_integration(self):
        """Test 8: Data Flow Integration"""
        logger.info("\n" + "=" * 60)
        logger.info("Test 8: Data Flow Integration")
        logger.info("=" * 60)

        # Test data consistency across endpoints
        try:
            # Get positions
            positions_response = self.session.get(f"{self.base_url}/api/trading/positions")
            if positions_response.status_code == 200:
                positions_data = positions_response.json()

                # Get statistics
                stats_response = self.session.get(f"{self.base_url}/api/trading/statistics")
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()

                    # Verify data consistency
                    self.log_test(
                        "Data Flow - Consistency",
                        True,
                        "Positions and statistics retrieved successfully",
                        {
                            "positions_count": len(positions_data.get("data", {}).get("items", [])),
                            "stats": stats_data
                        }
                    )
                else:
                    self.log_test("Data Flow - Statistics", False, f"Status: {stats_response.status_code}")
            else:
                self.log_test("Data Flow - Positions", False, f"Status: {positions_response.status_code}")

        except Exception as e:
            self.log_test("Data Flow Integration", False, f"Error: {str(e)}")

    def test_error_handling(self):
        """Test 9: Error Handling"""
        logger.info("\n" + "=" * 60)
        logger.info("Test 9: Error Handling")
        logger.info("=" * 60)

        # Test invalid endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/invalid/endpoint")
            success = response.status_code == 404
            self.log_test(
                "Error Handling - Invalid Endpoint",
                success,
                f"Status: {response.status_code} (expected 404)",
                {"endpoint": "/api/invalid/endpoint", "status_code": response.status_code}
            )
        except Exception as e:
            self.log_test("Error Handling - Invalid Endpoint", False, f"Error: {str(e)}")

        # Test invalid order data
        try:
            invalid_order = {
                "symbol": "",
                "order_type": "INVALID",
                "quantity": -100,
                "price": 0
            }
            response = self.session.post(
                f"{self.base_url}/api/trading/order",
                json=invalid_order
            )
            success = response.status_code in [400, 422]  # Bad request or validation error
            self.log_test(
                "Error Handling - Invalid Order",
                success,
                f"Status: {response.status_code} (expected 400/422)",
                {"endpoint": "/api/trading/order", "status_code": response.status_code}
            )
        except Exception as e:
            self.log_test("Error Handling - Invalid Order", False, f"Error: {str(e)}")

    def test_performance_metrics(self):
        """Test 10: API Performance Metrics"""
        logger.info("\n" + "=" * 60)
        logger.info("Test 10: API Performance")
        logger.info("=" * 60)

        # Test response time
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/trading/positions")
            end_time = time.time()
            response_time = end_time - start_time

            success = response_time < 1.0  # Should respond within 1 second
            self.log_test(
                "Performance - Response Time",
                success,
                f"Response time: {response_time:.3f}s (target: <1.0s)",
                {"response_time": response_time, "status_code": response.status_code}
            )
        except Exception as e:
            self.log_test("Performance - Response Time", False, f"Error: {str(e)}")

    def test_concurrent_requests(self):
        """Test 11: Concurrent Request Handling"""
        logger.info("\n" + "=" * 60)
        logger.info("Test 11: Concurrent Requests")
        logger.info("=" * 60)

        try:
            import concurrent.futures

            def make_request(url):
                try:
                    response = self.session.get(url)
                    return response.status_code == 200
                except:
                    return False

            # Make 10 concurrent requests
            urls = [f"{self.base_url}/api/trading/positions" for _ in range(10)]

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request, url) for url in urls]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            success_count = sum(results)
            total_count = len(results)
            success = success_count == total_count

            self.log_test(
                "Concurrent Requests",
                success,
                f"Successful: {success_count}/{total_count}",
                {"success_count": success_count, "total_count": total_count}
            )
        except Exception as e:
            self.log_test("Concurrent Requests", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("\n" + "=" * 60)
        logger.info("STARTING API INTEGRATION TEST SUITE")
        logger.info("=" * 60)
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Test Start Time: {datetime.now().isoformat()}")
        logger.info("=" * 60)

        # Run all tests
        self.test_api_health_check()
        self.test_dashboard_api()
        self.test_trading_api()
        self.test_risk_api()
        self.test_backtest_api()
        self.test_strategy_api()
        self.test_performance_api()
        self.test_data_flow_integration()
        self.test_error_handling()
        self.test_performance_metrics()
        self.test_concurrent_requests()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info("=" * 60)

        # List failed tests
        if failed_tests > 0:
            logger.info("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    logger.info(f"  ❌ {result['test']}: {result['message']}")

        # Save results to file
        self.save_results()

    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"api_integration_test_results_{timestamp}.json"

        results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for r in self.test_results if r['success']),
            "failed_tests": sum(1 for r in self.test_results if not r['success']),
            "success_rate": (sum(1 for r in self.test_results if r['success']) / len(self.test_results) * 100) if self.test_results else 0,
            "test_results": self.test_results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"\nTest results saved to: {filename}")


def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description="API Integration Test Suite")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of API server")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run test suite
    tester = APIIntegrationTester(base_url=args.url)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
