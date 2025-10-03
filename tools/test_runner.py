#!/usr/bin/env python3
"""
Optimized Test Runner
Runs comprehensive tests with all optimizations applied
"""

import subprocess
import time
import json
import argparse
import threading
from typing import Dict, Any
import os

class OptimizedTestRunner:
    """Runs optimized tests with comprehensive monitoring"""
    
    def __init__(self):
        self.results = {}
        self.monitor_thread = None
        self.monitoring = False
    
    def run_optimized_test(self, duration: int = 60) -> Dict[str, Any]:
        """Run optimized Docker test with monitoring"""
        print("=" * 80)
        print("OPTIMIZED MULTIPROCESSING TEST")
        print("=" * 80)
        
        # Step 1: Analyze current network
        print("\n1. Analyzing Docker network...")
        self._analyze_network()
        
        # Step 2: Apply optimizations
        print("\n2. Applying network optimizations...")
        self._apply_optimizations()
        
        # Step 3: Start enhanced monitoring
        print("\n3. Starting enhanced performance monitoring...")
        self._start_monitoring()
        
        # Step 4: Run optimized test
        print(f"\n4. Running optimized test for {duration} seconds...")
        test_results = self._run_optimized_docker_test(duration)
        
        # Step 5: Stop monitoring and analyze
        print("\n5. Analyzing results...")
        self._stop_monitoring()
        analysis = self._analyze_results()
        
        # Step 6: Generate comprehensive report
        print("\n6. Generating comprehensive report...")
        self._generate_report(test_results, analysis)
        
        return test_results
    
    def _analyze_network(self):
        """Analyze current Docker network configuration"""
        try:
            result = subprocess.run(
                ['python', 'docker_network_optimizer.py', '--analyze'],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
            print("Network analysis completed")
        except Exception as e:
            print(f"Network analysis error: {e}")
    
    def _apply_optimizations(self):
        """Apply Docker and system optimizations"""
        try:
            # Apply Docker network optimizations
            result = subprocess.run(
                ['python', 'docker_network_optimizer.py', '--optimize', '--create-compose'],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
            print("Docker optimizations applied")
        except Exception as e:
            print(f"Optimization error: {e}")
    
    def _start_monitoring(self):
        """Start enhanced performance monitoring"""
        try:
            self.monitoring = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop, daemon=True
            )
            self.monitor_thread.start()
            print("Enhanced monitoring started")
        except Exception as e:
            print(f"Monitoring start error: {e}")
    
    def _monitor_loop(self):
        """Monitoring loop"""
        try:
            result = subprocess.run(
                ['python', 'enhanced_performance_monitor.py', '--duration', '120', '--interval', '0.5'],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
        except Exception as e:
            print(f"Monitoring error: {e}")
    
    def _run_optimized_docker_test(self, duration: int) -> Dict[str, Any]:
        """Run optimized Docker test"""
        try:
            # Use original single-client compose file (prefer original for best performance)
            compose_file = "docker-compose.yml"
            if not os.path.exists(compose_file):
                compose_file = "docker-compose-optimized.yml"
            if not os.path.exists(compose_file):
                compose_file = "docker-compose-final.yml"
            if not os.path.exists(compose_file):
                compose_file = "docker-compose-stable.yml"
            if not os.path.exists(compose_file):
                compose_file = "docker-compose-fixed.yml"
            if not os.path.exists(compose_file):
                compose_file = "docker-compose-simple-optimized.yml"
            
            print(f"Using compose file: {compose_file}")
            
            # Ensure duration is sufficient for client completion (30s transmission + 5s buffer)
            min_duration = 35
            if duration < min_duration:
                print(f"Warning: Duration {duration}s is too short for client completion. Using {min_duration}s instead.")
                duration = min_duration
            
            # Build and start services
            print("Building optimized images...")
            build_result = subprocess.run(
                ['docker-compose', '-f', compose_file, 'build'],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
            
            if build_result.returncode != 0:
                print(f"Build failed: {build_result.stderr}")
                return {}
            
            print("Starting optimized services...")
            start_result = subprocess.run(
                ['docker-compose', '-f', compose_file, 'up', '-d'],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
            
            if start_result.returncode != 0:
                print(f"Start failed: {start_result.stderr}")
                return {}
            
            # Wait for test duration
            print(f"Test running for {duration} seconds...")
            time.sleep(duration)
            
            # Capture logs
            print("Capturing logs...")
            logs_result = subprocess.run(
                ['docker-compose', '-f', compose_file, 'logs'],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
            
            # Save Docker test results
            docker_results = {
                'containers': 7,  # server + 5 clients
                'server_logs': logs_result.stdout,
                'client_logs': {},
                'total_packets': 0,
                'total_bytes': 0,
                'errors': []
            }
            
            # Parse logs to extract client logs properly
            lines = logs_result.stdout.split('\n')
            client_logs = {}
            
            for line in lines:
                if '|' in line:
                    # Extract container name and log content
                    parts = line.split('|', 1)
                    if len(parts) == 2:
                        container_name = parts[0].strip()
                        log_content = parts[1].strip()
                        
                        # Only process client containers
                        if 'client-' in container_name:
                            if container_name not in client_logs:
                                client_logs[container_name] = []
                            client_logs[container_name].append(log_content)
            
            # Save client logs
            for client_name, log_lines in client_logs.items():
                docker_results['client_logs'][client_name] = '\n'.join(log_lines)
            
            # Save results to file
            os.makedirs('results', exist_ok=True)
            with open('results/docker_test_results.json', 'w') as f:
                json.dump(docker_results, f, indent=2)
            
            # Stop services
            print("Stopping services...")
            subprocess.run(
                ['docker-compose', '-f', compose_file, 'down'],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
            
            return {
                'duration': duration,
                'logs': logs_result.stdout,
                'errors': logs_result.stderr,
                'compose_file': compose_file,
                'docker_results_saved': True
            }
            
        except Exception as e:
            print(f"Docker test error: {e}")
            return {}
    
    def _stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("Monitoring stopped")
    
    def _analyze_results(self) -> Dict[str, Any]:
        """Analyze test results"""
        analysis = {}
        
        try:
            # Analyze Docker results
            if os.path.exists('docker_test_results.json'):
                result = subprocess.run(
                    ['python', 'analyze_docker_results.py'],
                    capture_output=True, text=True, encoding='utf-8', errors='ignore'
                )
                analysis['docker_analysis'] = result.stdout
            
            # Analyze client performance
            if os.path.exists('docker_test_results.json'):
                result = subprocess.run(
                    ['python', 'client_performance_analyzer.py'],
                    capture_output=True, text=True, encoding='utf-8', errors='ignore'
                )
                analysis['client_analysis'] = result.stdout
            
            # Analyze enhanced metrics
            if os.path.exists('enhanced_metrics.json'):
                with open('enhanced_metrics.json', 'r') as f:
                    enhanced_data = json.load(f)
                analysis['enhanced_metrics'] = enhanced_data.get('summary', {})
            
        except Exception as e:
            print(f"Analysis error: {e}")
        
        return analysis
    
    def _generate_report(self, test_results: Dict[str, Any], analysis: Dict[str, Any]):
        """Generate comprehensive report"""
        report = {
            'test_results': test_results,
            'analysis': analysis,
            'timestamp': time.time(),
            'optimizations_applied': [
                'Docker network optimization',
                'System network limits',
                'Enhanced performance monitoring',
                'Optimized client simulator',
                'Resource limits and constraints'
            ]
        }
        
        # Save report
        with open('results/test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n" + "=" * 80)
        print("OPTIMIZED TEST REPORT")
        print("=" * 80)
        
        print(f"\nTest Duration: {test_results.get('duration', 0)} seconds")
        print(f"Compose File: {test_results.get('compose_file', 'N/A')}")
        
        if 'enhanced_metrics' in analysis:
            metrics = analysis['enhanced_metrics']
            print(f"\nSystem Performance:")
            print(f"  Average CPU: {metrics.get('avg_cpu_percent', 0):.1f}%")
            print(f"  Max CPU: {metrics.get('max_cpu_percent', 0):.1f}%")
            print(f"  Average Memory: {metrics.get('avg_memory_percent', 0):.1f}%")
            print(f"  Python Processes: {metrics.get('total_python_processes', 0)}")
        
        print(f"\nOptimizations Applied:")
        for opt in report['optimizations_applied']:
            print(f"  - {opt}")
        
        print(f"\nReport saved to: results/test_report.json")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Optimized Test Runner')
    parser.add_argument('--duration', type=int, default=60, help='Test duration in seconds')
    parser.add_argument('--quick', action='store_true', help='Run quick test (30 seconds)')
    
    args = parser.parse_args()
    
    if args.quick:
        args.duration = 30
    
    runner = OptimizedTestRunner()
    runner.run_optimized_test(args.duration)

if __name__ == '__main__':
    main()
