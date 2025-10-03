#!/usr/bin/env python3
"""
Multiprocessing Server for High-Frequency Data Processing
Handles up to 10 client connections with 32-byte packets at 10kHz
"""

import socket
import multiprocessing as mp
import threading
import time
import json
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
from queue import Queue, Empty
import signal
import sys
import os
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ClientStats:
    """Statistics for a client connection"""
    client_id: str
    packets_received: int = 0
    bytes_received: int = 0
    start_time: float = 0
    last_packet_time: float = 0
    avg_packet_rate: float = 0
    
    def update_rate(self):
        """Calculate average packet rate"""
        if self.start_time > 0:
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                self.avg_packet_rate = self.packets_received / elapsed

class WorkerProcess:
    """Worker process to handle client connections"""
    
    def __init__(self, worker_id: int, stats_queue: mp.Queue):
        self.worker_id = worker_id
        self.stats_queue = stats_queue
        self.clients: Dict[str, ClientStats] = {}
        self.running = True
        
    def handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Handle a single client connection"""
        client_id = f"{client_address[0]}:{client_address[1]}"
        logger.info(f"Worker {self.worker_id} handling client {client_id}")
        
        # Initialize client stats
        client_stats = ClientStats(
            client_id=client_id,
            start_time=time.time()
        )
        self.clients[client_id] = client_stats
        
        try:
            while self.running:
                # Receive 32-byte packet
                data = client_socket.recv(32)
                if not data:
                    break
                    
                # Update statistics
                client_stats.packets_received += 1
                client_stats.bytes_received += len(data)
                client_stats.last_packet_time = time.time()
                client_stats.update_rate()
                
                # Send stats to main process periodically
                if client_stats.packets_received % 100 == 0:
                    self.stats_queue.put({
                        'worker_id': self.worker_id,
                        'client_id': client_id,
                        'stats': {
                            'packets_received': client_stats.packets_received,
                            'bytes_received': client_stats.bytes_received,
                            'avg_packet_rate': client_stats.avg_packet_rate
                        }
                    })
                
                # Simulate some processing (optional)
                # time.sleep(0.0001)  # 0.1ms processing time
                
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            client_socket.close()
            logger.info(f"Client {client_id} disconnected from worker {self.worker_id}")
            if client_id in self.clients:
                del self.clients[client_id]

def worker_process(worker_id: int, connection_queue: mp.Queue, stats_queue: mp.Queue):
    """Worker process function"""
    # Set worker process priority for better performance
    try:
        current_process = psutil.Process()
        current_process.nice(psutil.HIGH_PRIORITY_CLASS)
        print(f"Worker {worker_id}: Set high process priority")
    except Exception as e:
        print(f"Worker {worker_id}: Could not set process priority: {e}")
    
    logger.info(f"Worker process {worker_id} started")
    worker = WorkerProcess(worker_id, stats_queue)
    
    while True:
        try:
            # Get connection from queue
            connection_data = connection_queue.get(timeout=1.0)
            if connection_data is None:  # Shutdown signal
                break
                
            client_socket, client_address = connection_data
            worker.handle_client(client_socket, client_address)
            
        except Empty:
            continue
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}")
    
    logger.info(f"Worker process {worker_id} shutting down")

class MultiprocessingServer:
    """Main server class with multiprocessing support"""
    
    def __init__(self, host: str = 'localhost', port: int = 8888, 
                 num_workers: int = None, max_clients: int = 10):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.num_workers = num_workers or min(mp.cpu_count(), max_clients)
        
        # Multiprocessing components
        self.connection_queue = mp.Queue(maxsize=max_clients * 2)
        self.stats_queue = mp.Queue()
        self.worker_processes: List[mp.Process] = []
        
        # Server socket
        self.server_socket = None
        self.running = False
        
        # Statistics
        self.total_packets = 0
        self.total_bytes = 0
        self.start_time = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def start_workers(self):
        """Start worker processes"""
        logger.info(f"Starting {self.num_workers} worker processes")
        
        for i in range(self.num_workers):
            process = mp.Process(
                target=worker_process,
                args=(i, self.connection_queue, self.stats_queue)
            )
            process.start()
            self.worker_processes.append(process)
            logger.info(f"Started worker process {i} (PID: {process.pid})")
    
    def stop_workers(self):
        """Stop all worker processes"""
        logger.info("Stopping worker processes...")
        
        # Send shutdown signals to workers
        for _ in self.worker_processes:
            self.connection_queue.put(None)
        
        # Wait for workers to finish
        for process in self.worker_processes:
            process.join(timeout=5)
            if process.is_alive():
                logger.warning(f"Force killing worker process {process.pid}")
                process.terminate()
                process.join()
        
        self.worker_processes.clear()
        logger.info("All worker processes stopped")
    
    def start(self):
        """Start the server"""
        logger.info(f"Starting multiprocessing server on {self.host}:{self.port}")
        logger.info(f"Workers: {self.num_workers}, Max clients: {self.max_clients}")
        
        # Start worker processes
        self.start_workers()
        
        # Create server socket with optimizations
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Enhanced socket optimizations for high-performance server
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)  # 128KB receive buffer
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)  # 128KB send buffer
        
        # Set socket to non-blocking for better performance
        self.server_socket.setblocking(False)
        
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_clients)
        
        self.running = True
        self.start_time = time.time()
        
        # Start statistics monitoring thread
        stats_thread = threading.Thread(target=self._monitor_stats, daemon=True)
        stats_thread.start()
        
        logger.info("Server started, waiting for connections...")
        
        try:
            while self.running:
                try:
                    # Non-blocking accept with retry logic
                    client_socket, client_address = self.server_socket.accept()
                    logger.info(f"New connection from {client_address}")
                    
                    # Optimize client socket
                    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)
                    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
                    
                    # Dispatch to worker via queue
                    self.connection_queue.put((client_socket, client_address))
                    
                except BlockingIOError:
                    # No connection available, continue
                    time.sleep(0.001)  # 1ms sleep to prevent busy waiting
                    continue
                except socket.error as e:
                    if self.running:
                        logger.error(f"Socket error: {e}")
                    break
                    
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the server"""
        logger.info("Stopping server...")
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
        
        self.stop_workers()
        logger.info("Server stopped")
    
    def _monitor_stats(self):
        """Monitor and display statistics"""
        worker_stats = {}  # Track per-worker stats to calculate deltas
        
        while self.running:
            try:
                # Collect stats from workers
                stats_data = self.stats_queue.get(timeout=1.0)
                
                worker_id = stats_data['worker_id']
                client_id = stats_data['client_id']
                current_packets = stats_data['stats']['packets_received']
                current_bytes = stats_data['stats']['bytes_received']
                
                # Calculate delta from previous stats
                worker_key = f"{worker_id}_{client_id}"
                if worker_key in worker_stats:
                    prev_packets, prev_bytes = worker_stats[worker_key]
                    packet_delta = current_packets - prev_packets
                    byte_delta = current_bytes - prev_bytes
                    
                    # Only add positive deltas to avoid double counting
                    if packet_delta > 0:
                        self.total_packets += packet_delta
                    if byte_delta > 0:
                        self.total_bytes += byte_delta
                
                # Update worker stats
                worker_stats[worker_key] = (current_packets, current_bytes)
                
                # Display periodic stats
                elapsed = time.time() - self.start_time
                if elapsed > 0:
                    total_rate = self.total_packets / elapsed
                    logger.info(
                        f"Total: {self.total_packets} packets, "
                        f"{self.total_bytes} bytes, "
                        f"Rate: {total_rate:.1f} packets/sec"
                    )
                    
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Stats monitoring error: {e}")

def main():
    """Main function"""
    import argparse
    
    # Set process priority for better performance
    try:
        current_process = psutil.Process()
        current_process.nice(psutil.HIGH_PRIORITY_CLASS)
        print("Set high process priority for better performance")
    except Exception as e:
        print(f"Could not set process priority: {e}")
    
    # Set process affinity to use all available cores
    try:
        import multiprocessing
        os.sched_setaffinity(0, range(multiprocessing.cpu_count()))
        print(f"Set process affinity to {multiprocessing.cpu_count()} cores")
    except Exception as e:
        print(f"Could not set process affinity: {e}")
    
    parser = argparse.ArgumentParser(description='Multiprocessing Server')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=8888, help='Server port')
    parser.add_argument('--workers', type=int, help='Number of worker processes')
    parser.add_argument('--max-clients', type=int, default=10, help='Maximum clients')
    
    args = parser.parse_args()
    
    server = MultiprocessingServer(
        host=args.host,
        port=args.port,
        num_workers=args.workers,
        max_clients=args.max_clients
    )
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        server.stop()

if __name__ == '__main__':
    main()
