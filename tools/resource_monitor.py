#!/usr/bin/env python3
"""
Resource Monitoring Tool
Monitors Docker container resource usage during tests
"""

import subprocess
import json
import time
import threading
from typing import Dict, List, Any
import psutil

class ResourceMonitor:
    """Monitor Docker container resources"""
    
    def __init__(self):
        self.monitoring = False
        self.resource_data = []
        self.system_data = []
    
    def start_monitoring(self, duration: int = 35):
        """Start monitoring resources"""
        self.monitoring = True
        self.resource_data = []
        self.system_data = []
        
        print("Starting resource monitoring...")
        
        # Start monitoring threads
        docker_thread = threading.Thread(target=self._monitor_docker_resources, args=(duration,))
        system_thread = threading.Thread(target=self._monitor_system_resources, args=(duration,))
        
        docker_thread.start()
        system_thread.start()
        
        # Wait for monitoring to complete
        docker_thread.join()
        system_thread.join()
        
        return self._generate_report()
    
    def _monitor_docker_resources(self, duration: int):
        """Monitor Docker container resources"""
        start_time = time.time()
        
        while self.monitoring and (time.time() - start_time) < duration:
            try:
                # Get Docker stats
                result = subprocess.run(
                    ['docker', 'stats', '--no-stream', '--format', 
                     'json'],
                    capture_output=True, text=True, encoding='utf-8', errors='ignore'
                )
                
                if result.returncode == 0:
                    # Parse JSON output
                    lines = result.stdout.strip().split('\n')
                    container_stats = []
                    
                    for line in lines:
                        if line.strip():
                            try:
                                stats = json.loads(line)
                                container_stats.append(stats)
                            except json.JSONDecodeError:
                                continue
                    
                    if container_stats:
                        self.resource_data.append({
                            'timestamp': time.time(),
                            'containers': container_stats
                        })
                
                time.sleep(2)  # Sample every 2 seconds
                
            except Exception as e:
                print(f"Docker monitoring error: {e}")
                time.sleep(2)
    
    def _monitor_system_resources(self, duration: int):
        """Monitor system resources"""
        start_time = time.time()
        
        while self.monitoring and (time.time() - start_time) < duration:
            try:
                # Get system stats
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                self.system_data.append({
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available': memory.available,
                    'disk_percent': disk.percent
                })
                
                time.sleep(2)  # Sample every 2 seconds
                
            except Exception as e:
                print(f"System monitoring error: {e}")
                time.sleep(2)
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate resource usage report"""
        if not self.resource_data and not self.system_data:
            return {}
        
        report = {
            'monitoring_duration': len(self.resource_data) * 2,  # 2 second intervals
            'docker_stats': self._analyze_docker_stats(),
            'system_stats': self._analyze_system_stats(),
            'recommendations': []
        }
        
        # Generate recommendations
        self._generate_recommendations(report)
        
        return report
    
    def _analyze_docker_stats(self) -> Dict[str, Any]:
        """Analyze Docker container statistics"""
        if not self.resource_data:
            return {}
        
        container_analysis = {}
        all_cpu_usage = []
        all_memory_usage = []
        
        for sample in self.resource_data:
            for container in sample['containers']:
                container_name = container.get('Name', 'unknown')
                
                if container_name not in container_analysis:
                    container_analysis[container_name] = {
                        'cpu_samples': [],
                        'memory_samples': [],
                        'network_samples': []
                    }
                
                # Parse CPU usage
                cpu_str = container.get('CPUPerc', '0%').replace('%', '')
                try:
                    cpu_usage = float(cpu_str)
                    container_analysis[container_name]['cpu_samples'].append(cpu_usage)
                    all_cpu_usage.append(cpu_usage)
                except:
                    pass
                
                # Parse memory usage
                memory_str = container.get('MemUsage', '0B / 0B').split(' / ')[0]
                try:
                    if 'GiB' in memory_str:
                        memory_mb = float(memory_str.replace('GiB', '')) * 1024
                    elif 'MiB' in memory_str:
                        memory_mb = float(memory_str.replace('MiB', ''))
                    else:
                        memory_mb = float(memory_str.replace('B', '')) / (1024 * 1024)
                    
                    container_analysis[container_name]['memory_samples'].append(memory_mb)
                    all_memory_usage.append(memory_mb)
                except:
                    pass
        
        # Calculate averages and peaks
        analysis = {}
        for container_name, data in container_analysis.items():
            if data['cpu_samples']:
                analysis[container_name] = {
                    'avg_cpu': sum(data['cpu_samples']) / len(data['cpu_samples']),
                    'max_cpu': max(data['cpu_samples']),
                    'avg_memory_mb': sum(data['memory_samples']) / len(data['memory_samples']),
                    'max_memory_mb': max(data['memory_samples']) if data['memory_samples'] else 0
                }
        
        return {
            'containers': analysis,
            'overall_avg_cpu': sum(all_cpu_usage) / len(all_cpu_usage) if all_cpu_usage else 0,
            'overall_max_cpu': max(all_cpu_usage) if all_cpu_usage else 0,
            'overall_avg_memory_mb': sum(all_memory_usage) / len(all_memory_usage) if all_memory_usage else 0,
            'overall_max_memory_mb': max(all_memory_usage) if all_memory_usage else 0
        }
    
    def _analyze_system_stats(self) -> Dict[str, Any]:
        """Analyze system statistics"""
        if not self.system_data:
            return {}
        
        cpu_samples = [s['cpu_percent'] for s in self.system_data]
        memory_samples = [s['memory_percent'] for s in self.system_data]
        
        return {
            'avg_cpu_percent': sum(cpu_samples) / len(cpu_samples),
            'max_cpu_percent': max(cpu_samples),
            'avg_memory_percent': sum(memory_samples) / len(memory_samples),
            'max_memory_percent': max(memory_samples),
            'samples': len(self.system_data)
        }
    
    def _generate_recommendations(self, report: Dict[str, Any]):
        """Generate resource usage recommendations"""
        recommendations = []
        
        # Check Docker resource usage
        docker_stats = report.get('docker_stats', {})
        if docker_stats:
            overall_avg_cpu = docker_stats.get('overall_avg_cpu', 0)
            overall_max_cpu = docker_stats.get('overall_max_cpu', 0)
            
            if overall_max_cpu > 80:
                recommendations.append("High CPU usage detected - consider reducing client rates or increasing CPU limits")
            elif overall_avg_cpu < 20:
                recommendations.append("Low CPU usage - could increase client rates or reduce CPU limits")
            
            # Check individual containers
            for container_name, stats in docker_stats.get('containers', {}).items():
                if stats.get('max_cpu', 0) > 90:
                    recommendations.append(f"Container {container_name} hitting CPU limits - consider resource adjustment")
        
        # Check system resources
        system_stats = report.get('system_stats', {})
        if system_stats:
            max_memory = system_stats.get('max_memory_percent', 0)
            if max_memory > 85:
                recommendations.append("High system memory usage - consider increasing Docker memory allocation")
        
        report['recommendations'] = recommendations

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Resource Monitor')
    parser.add_argument('--duration', type=int, default=35, help='Monitoring duration in seconds')
    parser.add_argument('--output', help='Output file for report')
    
    args = parser.parse_args()
    
    monitor = ResourceMonitor()
    report = monitor.start_monitoring(args.duration)
    
    if report:
        print("\n" + "="*80)
        print("RESOURCE USAGE REPORT")
        print("="*80)
        
        # Docker stats
        docker_stats = report.get('docker_stats', {})
        if docker_stats:
            print(f"\nDocker Container Analysis:")
            print(f"  Overall Avg CPU: {docker_stats.get('overall_avg_cpu', 0):.1f}%")
            print(f"  Overall Max CPU: {docker_stats.get('overall_max_cpu', 0):.1f}%")
            print(f"  Overall Avg Memory: {docker_stats.get('overall_avg_memory_mb', 0):.1f} MB")
            print(f"  Overall Max Memory: {docker_stats.get('overall_max_memory_mb', 0):.1f} MB")
            
            print(f"\nIndividual Containers:")
            for container, stats in docker_stats.get('containers', {}).items():
                print(f"  {container}:")
                print(f"    Avg CPU: {stats.get('avg_cpu', 0):.1f}%")
                print(f"    Max CPU: {stats.get('max_cpu', 0):.1f}%")
                print(f"    Avg Memory: {stats.get('avg_memory_mb', 0):.1f} MB")
                print(f"    Max Memory: {stats.get('max_memory_mb', 0):.1f} MB")
        
        # System stats
        system_stats = report.get('system_stats', {})
        if system_stats:
            print(f"\nSystem Analysis:")
            print(f"  Avg CPU: {system_stats.get('avg_cpu_percent', 0):.1f}%")
            print(f"  Max CPU: {system_stats.get('max_cpu_percent', 0):.1f}%")
            print(f"  Avg Memory: {system_stats.get('avg_memory_percent', 0):.1f}%")
            print(f"  Max Memory: {system_stats.get('max_memory_percent', 0):.1f}%")
        
        # Recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            print(f"\nRecommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Save report
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to {args.output}")

if __name__ == '__main__':
    main()
