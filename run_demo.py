#!/usr/bin/env python3
"""
Demo Runner for Multiprocessing Server
Easy way to run the complete system demonstration
"""

import subprocess
import time
import threading
import logging
import sys
import os
import signal
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DemoRunner:
    """Runs a complete demonstration of the multiprocessing server"""
    
    def __init__(self):
        self.processes = []
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop_all()
        sys.exit(0)
    
    def start_server(self, workers: int = 4) -> subprocess.Popen:
        """Start the server process"""
        logger.info(f"Starting server with {workers} workers...")
        
        cmd = [
            sys.executable, "server.py",
            "--host", "localhost",
            "--port", "8888",
            "--workers", str(workers),
            "--max-clients", "10"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.processes.append(("server", process))
        time.sleep(2)  # Wait for server to start
        
        if process.poll() is None:
            logger.info("Server started successfully")
            return process
        else:
            logger.error("Server failed to start")
            return None
    
    def start_monitor(self) -> subprocess.Popen:
        """Start performance monitoring"""
        logger.info("Starting performance monitor...")
        
        cmd = [
            sys.executable, "performance_monitor.py",
            "--interval", "1.0",
            "--log-file", "demo_metrics.json"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.processes.append(("monitor", process))
        time.sleep(1)
        
        if process.poll() is None:
            logger.info("Performance monitor started")
            return process
        else:
            logger.error("Performance monitor failed to start")
            return None
    
    def start_clients(self, num_clients: int, packet_rate: float, 
                     duration: float) -> List[subprocess.Popen]:
        """Start client simulators"""
        logger.info(f"Starting {num_clients} clients at {packet_rate} Hz for {duration} seconds...")
        
        clients = []
        for i in range(num_clients):
            cmd = [
                sys.executable, "client_simulator.py",
                "--host", "localhost",
                "--port", "8888",
                "--clients", "1",
                "--rate", str(packet_rate),
                "--duration", str(duration)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            clients.append(process)
            self.processes.append((f"client_{i}", process))
            time.sleep(0.5)  # Stagger client starts
        
        logger.info(f"Started {num_clients} client processes")
        return clients
    
    def stop_all(self):
        """Stop all processes"""
        logger.info("Stopping all processes...")
        
        for name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"Stopped {name}")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.warning(f"Force killed {name}")
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
        
        self.processes.clear()
        self.running = False
    
    def run_demo(self, scenario: str = "basic"):
        """Run a demonstration scenario"""
        logger.info(f"Running demo scenario: {scenario}")
        
        try:
            if scenario == "basic":
                self._run_basic_demo()
            elif scenario == "multiprocess":
                self._run_multiprocess_demo()
            elif scenario == "stress":
                self._run_stress_demo()
            else:
                logger.error(f"Unknown scenario: {scenario}")
                return
            
        except KeyboardInterrupt:
            logger.info("Demo interrupted")
        finally:
            self.stop_all()
    
    def _run_basic_demo(self):
        """Run basic single-client demo"""
        logger.info("=== BASIC DEMO ===")
        logger.info("Single client, single worker, 1kHz")
        
        # Start server
        server = self.start_server(workers=1)
        if not server:
            return
        
        # Start monitor (optional)
        monitor = self.start_monitor()
        if not monitor:
            logger.warning("Performance monitor failed to start, continuing without monitoring")
        
        # Start single client
        clients = self.start_clients(num_clients=1, packet_rate=1000, duration=10)
        
        # Wait for completion
        logger.info("Demo running for 10 seconds...")
        time.sleep(12)
        
        logger.info("Basic demo completed")
    
    def _run_multiprocess_demo(self):
        """Run multiprocessing demo"""
        logger.info("=== MULTIPROCESS DEMO ===")
        logger.info("Multiple clients, multiple workers, 2kHz each")
        
        # Start server
        server = self.start_server(workers=4)
        if not server:
            return
        
        # Start monitor (optional)
        monitor = self.start_monitor()
        if not monitor:
            logger.warning("Performance monitor failed to start, continuing without monitoring")
        
        # Start multiple clients
        clients = self.start_clients(num_clients=4, packet_rate=2000, duration=15)
        
        # Wait for completion
        logger.info("Demo running for 15 seconds...")
        time.sleep(17)
        
        logger.info("Multiprocess demo completed")
    
    def _run_stress_demo(self):
        """Run stress test demo"""
        logger.info("=== STRESS DEMO ===")
        logger.info("High client count, limited workers, 1kHz each")
        
        # Start server
        server = self.start_server(workers=2)
        if not server:
            return
        
        # Start monitor (optional)
        monitor = self.start_monitor()
        if not monitor:
            logger.warning("Performance monitor failed to start, continuing without monitoring")
        
        # Start many clients
        clients = self.start_clients(num_clients=8, packet_rate=1000, duration=20)
        
        # Wait for completion
        logger.info("Demo running for 20 seconds...")
        time.sleep(22)
        
        logger.info("Stress demo completed")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Multiprocessing Server Demo')
    parser.add_argument('--scenario', choices=['basic', 'multiprocess', 'stress'], 
                       default='basic', help='Demo scenario to run')
    
    args = parser.parse_args()
    
    runner = DemoRunner()
    
    print("=" * 60)
    print("MULTIPROCESSING SERVER DEMONSTRATION")
    print("=" * 60)
    print(f"Scenario: {args.scenario}")
    print("Press Ctrl+C to stop at any time")
    print("=" * 60)
    
    runner.run_demo(args.scenario)
    
    print("=" * 60)
    print("DEMO COMPLETED")
    print("Check demo_metrics.json for performance data")
    print("=" * 60)

if __name__ == '__main__':
    main()
