#!/usr/bin/env python3
"""
Performance testing script for CI/CD Demo
This script runs various performance benchmarks and load tests
"""

import time
import requests
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import argparse
import sys

BASE_URL = "http://localhost:5000"

class PerformanceTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.results = {}
    
    def single_request_test(self, endpoint: str, method: str = 'GET', 
                          data: Dict = None, timeout: int = 10) -> Tuple[float, int]:
        """Perform a single request and return response time and status code"""
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = requests.get(f"{self.base_url}{endpoint}", timeout=timeout)
            elif method == 'POST':
                response = requests.post(f"{self.base_url}{endpoint}", 
                                       json=data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            return response_time, response.status_code
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return -1, 0
    
    def benchmark_endpoint(self, endpoint: str, method: str = 'GET', 
                          data: Dict = None, iterations: int = 10) -> Dict:
        """Benchmark an endpoint with multiple requests"""
        print(f"Benchmarking {method} {endpoint}...")
        
        response_times = []
        status_codes = []
        
        for i in range(iterations):
            response_time, status_code = self.single_request_test(endpoint, method, data)
            if response_time > 0:  # Only count successful requests
                response_times.append(response_time)
                status_codes.append(status_code)
            print(f"  Request {i+1}: {response_time:.3f}s, Status: {status_code}")
        
        if not response_times:
            return {"error": "All requests failed"}
        
        results = {
            'endpoint': endpoint,
            'method': method,
            'iterations': iterations,
            'successful_requests': len(response_times),
            'response_times': {
                'min': min(response_times),
                'max': max(response_times),
                'mean': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'stdev': statistics.stdev(response_times) if len(response_times) > 1 else 0
            },
            'status_codes': status_codes,
            'success_rate': len([c for c in status_codes if 200 <= c < 300]) / len(status_codes)
        }
        
        print(f"  Results: Mean={results['response_times']['mean']:.3f}s, "
              f"Min={results['response_times']['min']:.3f}s, "
              f"Max={results['response_times']['max']:.3f}s")
        
        return results
    
    def load_test(self, endpoint: str, concurrent_users: int = 10, 
                  duration: int = 30, method: str = 'GET', data: Dict = None) -> Dict:
        """Perform load testing with concurrent users"""
        print(f"Load testing {method} {endpoint} with {concurrent_users} users for {duration}s...")
        
        results = {
            'endpoint': endpoint,
            'method': method,
            'concurrent_users': concurrent_users,
            'duration': duration,
            'requests': [],
            'start_time': time.time()
        }
        
        def worker():
            """Worker function for concurrent requests"""
            end_time = time.time() + duration
            while time.time() < end_time:
                response_time, status_code = self.single_request_test(endpoint, method, data)
                if response_time > 0:
                    results['requests'].append({
                        'response_time': response_time,
                        'status_code': status_code,
                        'timestamp': time.time()
                    })
                time.sleep(0.1)  # Small delay between requests
        
        # Start concurrent workers
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(worker) for _ in range(concurrent_users)]
            for future in as_completed(futures):
                future.result()  # Wait for completion
        
        results['end_time'] = time.time()
        results['total_duration'] = results['end_time'] - results['start_time']
        results['total_requests'] = len(results['requests'])
        
        if results['total_requests'] > 0:
            response_times = [r['response_time'] for r in results['requests']]
            status_codes = [r['status_code'] for r in results['requests']]
            
            results['requests_per_second'] = results['total_requests'] / results['total_duration']
            results['response_times'] = {
                'min': min(response_times),
                'max': max(response_times),
                'mean': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'p95': sorted(response_times)[int(len(response_times) * 0.95)],
                'p99': sorted(response_times)[int(len(response_times) * 0.99)]
            }
            results['success_rate'] = len([c for c in status_codes if 200 <= c < 300]) / len(status_codes)
            results['error_distribution'] = {
                code: len([c for c in status_codes if c == code])
                for code in set(status_codes)
            }
        
        print(f"  Completed: {results['total_requests']} requests in {results['total_duration']:.1f}s")
        print(f"  RPS: {results.get('requests_per_second', 0):.1f}, "
              f"Success Rate: {results.get('success_rate', 0):.1%}")
        
        return results
    
    def run_comprehensive_tests(self) -> Dict:
        """Run comprehensive performance tests"""
        print("Starting comprehensive performance tests...\n")
        
        all_results = {
            'timestamp': time.time(),
            'base_url': self.base_url,
            'benchmarks': {},
            'load_tests': {}
        }
        
        # Benchmark tests
        endpoints_to_test = [
            ('/', 'GET'),
            ('/health', 'GET'),
            ('/api/stats', 'GET'),
            ('/api/deployments', 'GET'),
            ('/api/metrics/custom', 'GET'),
            ('/api/deployments', 'POST', {"version": "1.0.0", "environment": "test"})
        ]
        
        for endpoint_data in endpoints_to_test:
            if len(endpoint_data) == 2:
                endpoint, method = endpoint_data
                data = None
            else:
                endpoint, method, data = endpoint_data
            
            result = self.benchmark_endpoint(endpoint, method, data, iterations=5)
            all_results['benchmarks'][f"{method}_{endpoint}"] = result
            print()
        
        # Load tests
        load_test_configs = [
            ('/health', 'GET', None, 20, 30),   # 20 users for 30s
            ('/api/stats', 'GET', None, 10, 20), # 10 users for 20s
            ('/api/deployments', 'GET', None, 15, 25), # 15 users for 25s
        ]
        
        for endpoint, method, data, users, duration in load_test_configs:
            result = self.load_test(endpoint, users, duration, method, data)
            all_results['load_tests'][f"{method}_{endpoint}"] = result
            print()
        
        return all_results
    
    def save_results(self, results: Dict, filename: str = "performance_results.json"):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Performance testing for CI/CD Demo")
    parser.add_argument("--url", default=BASE_URL, help="Base URL to test")
    parser.add_argument("--benchmark-only", action="store_true", help="Run only benchmarks")
    parser.add_argument("--load-only", action="store_true", help="Run only load tests")
    parser.add_argument("--output", default="performance_results.json", help="Output file")
    parser.add_argument("--endpoint", help="Test specific endpoint")
    parser.add_argument("--users", type=int, default=10, help="Concurrent users for load test")
    parser.add_argument("--duration", type=int, default=30, help="Duration for load test (seconds)")
    
    args = parser.parse_args()
    
    tester = PerformanceTester(args.url)
    
    # Check if server is running
    try:
        response_time, status_code = tester.single_request_test('/health')
        if status_code != 200:
            print(f"Server is not responding correctly (status: {status_code})")
            sys.exit(1)
        print(f"Server is running at {args.url} (response time: {response_time:.3f}s)\n")
    except Exception as e:
        print(f"Cannot connect to server at {args.url}: {e}")
        sys.exit(1)
    
    if args.endpoint:
        # Test specific endpoint
        if args.load_only:
            results = tester.load_test(args.endpoint, args.users, args.duration)
        else:
            results = tester.benchmark_endpoint(args.endpoint, iterations=10)
        
        tester.save_results({'single_test': results}, args.output)
    elif args.benchmark_only:
        results = tester.run_comprehensive_tests()
        results['load_tests'] = {}  # Remove load tests
        tester.save_results(results, args.output)
    elif args.load_only:
        # Run only load tests
        print("Running load tests only...")
        results = {'timestamp': time.time(), 'load_tests': {}}
        
        load_endpoints = [
            ('/health', 'GET', None, args.users, args.duration),
            ('/api/stats', 'GET', None, args.users//2, args.duration),
        ]
        
        for endpoint, method, data, users, duration in load_endpoints:
            result = tester.load_test(endpoint, users, duration, method, data)
            results['load_tests'][f"{method}_{endpoint}"] = result
        
        tester.save_results(results, args.output)
    else:
        # Run comprehensive tests
        results = tester.run_comprehensive_tests()
        tester.save_results(results, args.output)
    
    print("\nPerformance testing completed!")

if __name__ == "__main__":
    main()
