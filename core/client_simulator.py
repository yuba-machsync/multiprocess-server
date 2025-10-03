#!/usr/bin/env python3
"""
Optimized Client Simulator
High-performance client with optimizations for 10kHz target
"""

import socket
import time
import threading
import argparse
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
import struct
import os

@dataclass
class ClientStats:
    """Client performance statistics"""
    packets_sent: int = 0
    bytes_sent: int = 0
    start_time: float = 0
    end_time: float = 0
    errors: int = 0
    avg_rate: float = 0.0

class OptimizedClient:
    """Optimized high-performance client"""
    
    def __init__(self, client_id: str, target_rate: float = 10000.0):
        self.client_id = client_id
        self.target_rate = target_rate
        self.socket = None
        self.stats = ClientStats()
        self.running = False
        self.thread = None
        
        # Performance optimizations
        self.packet_data = b'X' * 16  # Pre-allocated packet data (16 bytes)
        self.batch_size = 804  # Fixed batch size as per specifications
        self.send_timeout = 0.001  # 1ms timeout for non-blocking sends
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"Client-{client_id}")
    
    def connect(self, host: str, port: int) -> bool:
        """Connect to server with optimizations"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Enhanced socket optimizations for high-performance networking
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's algorithm
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)  # 128KB send buffer (increased)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)  # 128KB receive buffer (increased)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # Enable keep-alive
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
            
            # Set socket to non-blocking for better performance
            self.socket.setblocking(False)
            
            # Connect with timeout and retry logic
            max_retries = 10
            retry_delay = 0.5
            
            for attempt in range(max_retries):
                try:
                    self.socket.connect((host, port))
                    self.logger.info(f"Client {self.client_id} connected to {host}:{port} (attempt {attempt + 1})")
                    return True
                except (BlockingIOError, ConnectionRefusedError, OSError) as e:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Connection attempt {attempt + 1} failed: {e}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 1.5, 2.0)  # Exponential backoff
                        continue
                    else:
                        self.logger.error(f"All connection attempts failed: {e}")
                        return False
                except Exception as e:
                    self.logger.error(f"Unexpected connection error: {e}")
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def _reconnect(self) -> bool:
        """Attempt to reconnect to server"""
        try:
            if self.socket:
                self.socket.close()
            self.socket = None
            
            # Try to reconnect with the same parameters
            return self.connect("server", 8888)
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")
            return False
    
    def start_transmission(self, duration: float = 60.0):
        """Start optimized data transmission"""
        if not self.socket:
            self.logger.error("Not connected to server")
            return False
        
        self.stats.start_time = time.time()
        self.stats.end_time = self.stats.start_time + duration
        self.running = True
        
        # Start transmission thread
        self.thread = threading.Thread(target=self._transmission_loop, daemon=True)
        self.thread.start()
        
        self.logger.info(f"Client {self.client_id} starting transmission at {self.target_rate} Hz for {duration}s")
        return True
    
    def _transmission_loop(self):
        """Optimized transmission loop"""
        packet_interval = 1.0 / self.target_rate
        next_send_time = time.time()
        
        while self.running and time.time() < self.stats.end_time:
            current_time = time.time()
            
            # Batch sending for better performance
            if current_time >= next_send_time:
                self._send_batch()
                next_send_time += packet_interval * self.batch_size
            
            # Adaptive sleep to reduce CPU usage
            sleep_time = max(0.0001, (next_send_time - current_time) / 2)
            time.sleep(sleep_time)
        
        self._finalize_stats()
    
    def _send_batch(self):
        """Send a batch of packets for better performance"""
        try:
            # Enhanced batch sending with retry logic
            batch_data = self.packet_data * self.batch_size
            bytes_sent = 0
            retry_count = 0
            max_retries = 3
            
            while bytes_sent < len(batch_data) and retry_count < max_retries:
                try:
                    sent = self.socket.send(batch_data[bytes_sent:])
                    if sent == 0:
                        raise ConnectionError("Socket connection lost")
                    bytes_sent += sent
                    retry_count = 0  # Reset retry count on successful send
                except BlockingIOError:
                    # Socket buffer full, wait and retry
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(0.001)  # 1ms retry delay
                    else:
                        self.stats.errors += self.batch_size
                        break
                except ConnectionError as e:
                    self.logger.error(f"Connection lost: {e}")
                    # Try to reconnect
                    if self._reconnect():
                        self.logger.info("Reconnected successfully")
                        continue
                    else:
                        self.stats.errors += self.batch_size
                        break
                except Exception as e:
                    self.logger.error(f"Send error: {e}")
                    self.stats.errors += self.batch_size
                    break
            
            if bytes_sent > 0:
                self.stats.packets_sent += self.batch_size
                self.stats.bytes_sent += bytes_sent
                
        except Exception as e:
            self.stats.errors += self.batch_size
            if self.stats.errors % 1000 == 0:  # Log every 1000 errors
                self.logger.error(f"Batch send error: {e}")
    
    def _finalize_stats(self):
        """Calculate final statistics"""
        self.stats.end_time = time.time()
        duration = self.stats.end_time - self.stats.start_time
        
        if duration > 0:
            self.stats.avg_rate = self.stats.packets_sent / duration
        
        # Output detailed statistics in a format that analyzers can easily parse
        self.logger.info(f"Client {self.client_id} transmission completed:")
        self.logger.info(f"  Packets sent: {self.stats.packets_sent}")
        self.logger.info(f"  Bytes sent: {self.stats.bytes_sent}")
        self.logger.info(f"  Duration: {duration:.2f}s")
        self.logger.info(f"  Average rate: {self.stats.avg_rate:.1f} Hz")
        self.logger.info(f"  Errors: {self.stats.errors}")
        
        # Output final statistics in a structured format for easy parsing
        self.logger.info("=== CLIENT FINAL STATISTICS ===")
        self.logger.info(f"Total packets sent: {self.stats.packets_sent}")
        self.logger.info(f"Total bytes sent: {self.stats.bytes_sent}")
        self.logger.info(f"Duration: {duration:.2f}s")
        self.logger.info(f"Average rate: {self.stats.avg_rate:.1f} Hz")
        self.logger.info(f"Errors: {self.stats.errors}")
        self.logger.info("=== END CLIENT STATISTICS ===")
    
    def stop(self):
        """Stop transmission and close connection"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        
        if self.socket:
            self.socket.close()
            self.socket = None

class OptimizedClientSimulator:
    """Optimized client simulator with multiple clients"""
    
    def __init__(self, num_clients: int = 1, target_rate: float = 10000.0):
        self.num_clients = num_clients
        self.target_rate = target_rate
        self.clients: List[OptimizedClient] = []
        self.logger = logging.getLogger("ClientSimulator")
    
    def start_clients(self, host: str, port: int, duration: float = 60.0) -> bool:
        """Start all clients with optimizations"""
        self.logger.info(f"Starting {self.num_clients} optimized clients")
        self.logger.info(f"Target rate: {self.target_rate} Hz per client")
        self.logger.info(f"Total target rate: {self.target_rate * self.num_clients} Hz")
        
        # Create and connect clients
        for i in range(self.num_clients):
            client_id = f"client_{i:03d}"
            client = OptimizedClient(client_id, self.target_rate)
            
            if client.connect(host, port):
                self.clients.append(client)
                self.logger.info(f"Client {client_id} connected")
            else:
                self.logger.error(f"Client {client_id} connection failed")
        
        if not self.clients:
            self.logger.error("No clients connected")
            return False
        
        # Start transmission for all clients
        for client in self.clients:
            client.start_transmission(duration)
        
        self.logger.info("All clients started")
        return True
    
    def wait_for_completion(self):
        """Wait for all clients to complete"""
        for client in self.clients:
            if client.thread:
                client.thread.join()
    
    def stop_all(self):
        """Stop all clients"""
        for client in self.clients:
            client.stop()
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        if not self.clients:
            return {}
        
        total_packets = sum(c.stats.packets_sent for c in self.clients)
        total_bytes = sum(c.stats.bytes_sent for c in self.clients)
        total_errors = sum(c.stats.errors for c in self.clients)
        
        avg_rate = sum(c.stats.avg_rate for c in self.clients) / len(self.clients)
        
        return {
            'total_clients': len(self.clients),
            'total_packets': total_packets,
            'total_bytes': total_bytes,
            'total_errors': total_errors,
            'avg_rate_per_client': avg_rate,
            'total_rate': avg_rate * len(self.clients)
        }

def main():
    """Main function"""
    # Handle startup delay from environment variable
    startup_delay = int(os.environ.get('CLIENT_STARTUP_DELAY', '0'))
    if startup_delay > 0:
        print(f"Client startup delay: {startup_delay} seconds")
        time.sleep(startup_delay)
    
    # Set process priority for better performance
    try:
        import psutil
        current_process = psutil.Process()
        current_process.nice(psutil.HIGH_PRIORITY_CLASS)
        print("Set high process priority for better performance")
    except Exception as e:
        print(f"Could not set process priority: {e}")
    
    parser = argparse.ArgumentParser(description='Optimized Client Simulator')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=8888, help='Server port')
    parser.add_argument('--clients', type=int, default=1, help='Number of clients')
    parser.add_argument('--rate', type=float, default=10000.0, help='Target rate per client (Hz)')
    parser.add_argument('--duration', type=float, default=60.0, help='Test duration (seconds)')
    
    args = parser.parse_args()
    
    # Set process priority for better performance
    try:
        import psutil
        current_process = psutil.Process()
        current_process.nice(psutil.HIGH_PRIORITY_CLASS)
        print("Set high process priority for better performance")
    except:
        pass
    
    simulator = OptimizedClientSimulator(args.clients, args.rate)
    
    try:
        if simulator.start_clients(args.host, args.port, args.duration):
            simulator.wait_for_completion()
            
            # Print summary
            stats = simulator.get_summary_stats()
            print(f"\n=== OPTIMIZED CLIENT SUMMARY ===")
            print(f"Total clients: {stats['total_clients']}")
            print(f"Total packets: {stats['total_packets']:,}")
            print(f"Total bytes: {stats['total_bytes']:,}")
            print(f"Total errors: {stats['total_errors']}")
            print(f"Average rate per client: {stats['avg_rate_per_client']:.1f} Hz")
            print(f"Total rate: {stats['total_rate']:.1f} Hz")
            
        else:
            print("Failed to start clients")
            
    except KeyboardInterrupt:
        print("\nStopping clients...")
    finally:
        simulator.stop_all()

if __name__ == '__main__':
    main()
