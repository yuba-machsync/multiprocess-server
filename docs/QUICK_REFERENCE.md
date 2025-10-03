# Multiprocessing Server - Quick Reference Guide

## System Overview

A high-performance multiprocessing server system designed for handling multiple concurrent clients with high-frequency data transmission (10kHz, 32-byte packets).

## Quick Start

### 1. Basic Usage

```bash
# Start the system
python tools/test_runner.py --duration 60

# Analyze results
python tools/analyze_docker_results.py

# Run demo
python run_demo.py
```

### 2. Docker Commands

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop system
docker-compose down

# Clean up
docker-compose down -v --rmi all
```

## Architecture Components

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| **Server** | Main process, connection handling | `core/server.py` |
| **Client** | Data generation, transmission | `core/client_simulator.py` |
| **Monitor** | Performance tracking | `core/performance_monitor.py` |
| **Docker** | Containerization | `docker-compose.yml`, `Dockerfile` |
| **Tools** | Testing, analysis | `tools/test_runner.py`, `tools/analyze_docker_results.py` |

## Key Configuration

### Server Configuration
```python
# core/server.py
server = MultiprocessingServer(
    host='0.0.0.0',
    port=8888,
    num_workers=4,        # Number of worker processes
    max_clients=10        # Maximum concurrent clients
)
```

### Client Configuration
```python
# core/client_simulator.py
client = OptimizedClient(
    client_id='client_001',
    target_rate=6000.0    # Packets per second
)
```

### Docker Configuration
```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1.5G
    reservations:
      cpus: '1.5'
      memory: 1G
```

## Performance Metrics

### Expected Performance
- **Target Rate**: 10,050 packets/second per client
- **Packet Size**: 16 bytes
- **Batch Size**: 804 packets per batch
- **Concurrent Clients**: 5 clients
- **Total Throughput**: ~50,250 packets/second
- **Success Rate**: >99%

### Key Metrics
```python
# Server statistics
{
    'total_packets': 150000,
    'total_bytes': 4800000,
    'active_connections': 5,
    'errors': 0,
    'workers': 4
}

# Client statistics
{
    'packets_sent': 301500,
    'bytes_sent': 4824000,
    'rate': 10050.0,
    'errors': 0
}
```

## Troubleshooting

### Common Issues

#### 1. Connection Refused
```bash
# Check if server is running
docker ps | grep server

# Check server logs
docker logs multiprocess_test-server-1

# Check network connectivity
docker exec -it multiprocess_test-client-1-1 ping server
```

#### 2. Performance Issues
```bash
# Monitor resource usage
docker stats

# Check system resources
htop
iostat -x 1

# Analyze network performance
netstat -i
```

#### 3. Memory Issues
```bash
# Check memory usage
free -h
docker stats --no-stream

# Monitor memory leaks
valgrind --tool=memcheck python server.py
```

### Performance Optimization

#### 1. System-Level
```bash
# Increase file descriptor limits
ulimit -n 65536

# Optimize network parameters
echo 'net.core.rmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' >> /etc/sysctl.conf
sysctl -p
```

#### 2. Application-Level
```python
# Socket optimizations
socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)
socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)

# Process optimizations
psutil.Process().nice(psutil.HIGH_PRIORITY_CLASS)
os.sched_setaffinity(0, range(multiprocessing.cpu_count()))
```

## Integration Examples

### 1. Web Application Integration
```python
from flask import Flask, jsonify

app = Flask(__name__)
server = MultiprocessingServer('localhost', 8888)

@app.route('/status')
def get_status():
    return jsonify({
        'active_connections': server.stats.active_connections,
        'total_packets': server.stats.total_packets,
        'errors': server.stats.errors
    })
```

### 2. Database Integration
```python
import sqlite3

def log_stats(stats):
    with sqlite3.connect('stats.db') as conn:
        conn.execute('''
            INSERT INTO stats (packets, bytes, errors)
            VALUES (?, ?, ?)
        ''', (stats.packets, stats.bytes, stats.errors))
```

### 3. Message Queue Integration
```python
import redis

redis_client = redis.Redis()

def publish_stats(stats):
    redis_client.publish('server_stats', json.dumps(stats))
```

## Production Deployment

### 1. Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8888
CMD ["python", "server.py"]
```

### 2. Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multiprocessing-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: multiprocessing-server
  template:
    spec:
      containers:
      - name: server
        image: multiprocessing-server:latest
        ports:
        - containerPort: 8888
        resources:
          requests:
            memory: "2Gi"
            cpu: "2"
          limits:
            memory: "4Gi"
            cpu: "4"
```

### 3. Monitoring Setup
```python
from prometheus_client import Counter, Gauge, start_http_server

# Metrics
packets_processed = Counter('packets_processed_total', 'Total packets processed')
active_connections = Gauge('active_connections', 'Active connections')

# Start metrics server
start_http_server(8000)
```

## Development Workflow

### 1. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Run demo
python run_demo.py
```

### 2. Docker Development
```bash
# Build image
docker build -t multiprocessing-server .

# Run container
docker run -p 8888:8888 multiprocessing-server

# Debug container
docker exec -it <container_id> bash
```

### 3. Testing
```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Run performance tests
python tools/test_runner.py --duration 60
```

## File Structure

```
multiprocess_test/
├── core/                          # Core application files
│   ├── server.py                  # Multiprocessing server
│   ├── client_simulator.py       # Client simulator
│   └── performance_monitor.py     # Performance monitoring
├── tools/                         # Testing and analysis tools
│   ├── test_runner.py            # Test runner
│   ├── analyze_docker_results.py # Result analyzer
│   └── client_performance_analyzer.py # Performance analyzer
├── docs/                           # Documentation
│   ├── SYSTEM_ARCHITECTURE.md     # System architecture
│   ├── MULTIPROCESSING_IMPLEMENTATION.md # Implementation details
│   └── QUICK_REFERENCE.md        # This file
├── results/                       # Test results
│   ├── docker_test_results.json  # Docker test results
│   └── test_report.json          # Test reports
├── docker-compose.yml             # Docker orchestration
├── Dockerfile                     # Docker image definition
├── requirements.txt               # Python dependencies
└── README.md                      # Project documentation
```

## Key Classes and Methods

### Server Classes
```python
class MultiprocessingServer:
    def __init__(self, host, port, num_workers, max_clients)
    def start(self)
    def stop(self)
    def distribute_connection(self, client_socket, client_address)
    def collect_statistics(self)

def worker_process(worker_id, connection_queue, stats_queue)
def handle_client(client_socket, client_address, worker_id, stats_queue)
```

### Client Classes
```python
class OptimizedClient:
    def __init__(self, client_id, target_rate)
    def connect(self, host, port)
    def start_transmission(self, duration)
    def disconnect(self)
    def _send_batch(self)
    def _reconnect(self)
```

### Monitoring Classes
```python
class PerformanceMonitor:
    def __init__(self, duration)
    def start(self)
    def stop(self)
    def get_metrics(self)

class ClientStats:
    def __init__(self)
    def update(self, packets, bytes_sent)
    def get_rate(self)
```

## Configuration Parameters

### Server Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `host` | '0.0.0.0' | Server host address |
| `port` | 8888 | Server port |
| `num_workers` | 4 | Number of worker processes |
| `max_clients` | 10 | Maximum concurrent clients |

### Client Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `target_rate` | 10050.0 | Target packets per second |
| `packet_size` | 16 | Packet size in bytes |
| `batch_size` | 804 | Packets per batch |
| `duration` | 30 | Transmission duration in seconds |

### Docker Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `cpus` | '2.0' | CPU limit per container |
| `memory` | '1.5G' | Memory limit per container |
| `nofile` | 65536 | File descriptor limit |

## Performance Benchmarks

### System Requirements
- **CPU**: 4+ cores recommended
- **Memory**: 8GB+ RAM recommended
- **Network**: 1Gbps+ recommended
- **OS**: Linux preferred, Windows supported

### Expected Performance
- **Single Client**: 10,050 packets/second
- **5 Clients**: 50,250 packets/second
- **10 Clients**: 100,500 packets/second
- **Latency**: <1ms average
- **Error Rate**: <0.1%

### Resource Usage
- **Server Process**: ~200MB RAM, 1-2 CPU cores
- **Worker Process**: ~100MB RAM, 0.5-1 CPU core each
- **Client Process**: ~50MB RAM, 0.5 CPU core each

## Security Considerations

### Network Security
```python
# TLS/SSL integration
import ssl

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain('server.crt', 'server.key')
secure_socket = context.wrap_socket(socket, server_side=True)
```

### Authentication
```python
# Client authentication
def authenticate_client(client_socket):
    auth_token = client_socket.recv(1024)
    return validate_token(auth_token)
```

### Access Control
```python
# IP whitelist
ALLOWED_IPS = ['192.168.1.0/24', '10.0.0.0/8']

def is_allowed_ip(client_address):
    return any(ipaddress.ip_address(client_address[0]) in ipaddress.ip_network(net) 
               for net in ALLOWED_IPS)
```

## Monitoring and Alerting

### Key Metrics to Monitor
- **Connection Count**: Active connections
- **Packet Rate**: Packets per second
- **Error Rate**: Errors per second
- **Memory Usage**: RAM utilization
- **CPU Usage**: CPU utilization
- **Network I/O**: Bytes per second

### Alerting Thresholds
- **Error Rate**: >1% for 5 minutes
- **Memory Usage**: >80% for 5 minutes
- **CPU Usage**: >90% for 5 minutes
- **Connection Count**: >90% of max_clients

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
```

This quick reference guide provides essential information for developers working with the multiprocessing server system. For detailed implementation information, refer to the other documentation files in the `docs/` directory.
