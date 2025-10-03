#!/usr/bin/env python3
"""
Enhanced Performance Monitor
Monitors system resources during Docker tests with detailed analysis
"""

import psutil
import time
import json
import threading
import subprocess
import os
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import argparse

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_io_read: int
    disk_io_write: int
    network_sent: int
    network_recv: int
    docker_containers: int
    docker_cpu_percent: float
    docker_memory_mb: float

@dataclass
class ProcessMetrics:
    """Process-specific metrics"""
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    threads: int
    connections: int

class EnhancedPerformanceMonitor:
    """Enhanced system performance monitor"""
    
    def __init__(self, output_file: str = "enhanced_metrics.json"):
        self.output_file = output_file
        self.monitoring = False
        self.metrics_history: List[SystemMetrics] = []
        self.process_history: List[ProcessMetrics] = []
        self.monitor_thread = None
        
    def start_monitoring(self, interval: float = 1.0):
        """Start monitoring system resources"""
        if self.monitoring:
            return False
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        return True
    
    def stop_monitoring(self):
        """Stop monitoring and save results"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self._save_results()
    
    def _monitor_loop(self, interval: float):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.metrics_history.append(system_metrics)
                
                # Collect process metrics
                process_metrics = self._collect_process_metrics()
                self.process_history.extend(process_metrics)
                
                # Print real-time status
                self._print_status(system_metrics, process_metrics)
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-wide metrics"""
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        
        # Network I/O
        network_io = psutil.net_io_counters()
        
        # Docker metrics
        docker_containers, docker_cpu, docker_memory = self._get_docker_metrics()
        
        return SystemMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_available=memory.available,
            disk_io_read=disk_io.read_bytes if disk_io else 0,
            disk_io_write=disk_io.write_bytes if disk_io else 0,
            network_sent=network_io.bytes_sent,
            network_recv=network_io.bytes_recv,
            docker_containers=docker_containers,
            docker_cpu_percent=docker_cpu,
            docker_memory_mb=docker_memory
        )
    
    def _collect_process_metrics(self) -> List[ProcessMetrics]:
        """Collect process-specific metrics"""
        metrics = []
        
        # Monitor Python processes
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'num_threads']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    # Get process details
                    with proc.oneshot():
                        cpu_percent = proc.cpu_percent()
                        memory_info = proc.memory_info()
                        memory_mb = memory_info.rss / 1024 / 1024
                        threads = proc.num_threads()
                        
                        # Count network connections
                        connections = len(proc.connections()) if hasattr(proc, 'connections') else 0
                        
                        metrics.append(ProcessMetrics(
                            pid=proc.pid,
                            name=proc.name(),
                            cpu_percent=cpu_percent,
                            memory_mb=memory_mb,
                            threads=threads,
                            connections=connections
                        ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return metrics
    
    def _get_docker_metrics(self) -> tuple:
        """Get Docker container metrics"""
        try:
            # Count running containers
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
            containers = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            container_count = len(containers)
            
            # Get Docker stats
            if containers:
                result = subprocess.run(
                    ['docker', 'stats', '--no-stream', '--format', 
                     'table {{.CPUPerc}}\t{{.MemUsage}}'],
                    capture_output=True, text=True, encoding='utf-8', errors='ignore'
                )
                
                # Parse CPU and memory usage
                cpu_total = 0.0
                memory_total = 0.0
                
                for line in result.stdout.split('\n')[1:]:  # Skip header
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            try:
                                cpu_str = parts[0].replace('%', '')
                                cpu_total += float(cpu_str)
                                
                                mem_str = parts[1].split('/')[0].strip()
                                if 'MiB' in mem_str:
                                    memory_total += float(mem_str.replace('MiB', ''))
                                elif 'GiB' in mem_str:
                                    memory_total += float(mem_str.replace('GiB', '')) * 1024
                            except:
                                pass
                
                return container_count, cpu_total, memory_total
            else:
                return 0, 0.0, 0.0
                
        except Exception as e:
            print(f"Docker metrics error: {e}")
            return 0, 0.0, 0.0
    
    def _print_status(self, system_metrics: SystemMetrics, process_metrics: List[ProcessMetrics]):
        """Print real-time status"""
        print(f"\r[Monitor] CPU: {system_metrics.cpu_percent:.1f}% | "
              f"RAM: {system_metrics.memory_percent:.1f}% | "
              f"Docker: {system_metrics.docker_containers} containers | "
              f"Python procs: {len(process_metrics)}", end='', flush=True)
    
    def _save_results(self):
        """Save monitoring results to file"""
        results = {
            'system_metrics': [asdict(m) for m in self.metrics_history],
            'process_metrics': [asdict(p) for p in self.process_history],
            'summary': self._generate_summary()
        }
        
        with open(self.output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nEnhanced metrics saved to {self.output_file}")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate performance summary"""
        if not self.metrics_history:
            return {}
        
        # System summary
        cpu_values = [m.cpu_percent for m in self.metrics_history]
        memory_values = [m.memory_percent for m in self.metrics_history]
        
        # Process summary
        python_processes = [p for p in self.process_history if 'python' in p.name.lower()]
        
        return {
            'monitoring_duration': len(self.metrics_history),
            'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
            'max_cpu_percent': max(cpu_values),
            'avg_memory_percent': sum(memory_values) / len(memory_values),
            'max_memory_percent': max(memory_values),
            'total_python_processes': len(python_processes),
            'avg_python_cpu': sum(p.cpu_percent for p in python_processes) / len(python_processes) if python_processes else 0,
            'avg_python_memory': sum(p.memory_mb for p in python_processes) / len(python_processes) if python_processes else 0
        }

def main():
    """Main function for standalone monitoring"""
    parser = argparse.ArgumentParser(description='Enhanced Performance Monitor')
    parser.add_argument('--duration', type=int, default=60, 
                       help='Monitoring duration in seconds')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Monitoring interval in seconds')
    parser.add_argument('--output', default='enhanced_metrics.json',
                       help='Output file for metrics')
    
    args = parser.parse_args()
    
    monitor = EnhancedPerformanceMonitor(args.output)
    
    print(f"Starting enhanced performance monitoring for {args.duration}s...")
    monitor.start_monitoring(args.interval)
    
    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
    finally:
        monitor.stop_monitoring()
        print("Monitoring completed")

if __name__ == '__main__':
    main()
