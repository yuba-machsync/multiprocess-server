#!/usr/bin/env python3
"""
Client Performance Analyzer
Investigates individual client performance issues
"""

import json
import re
from typing import Dict, List, Any
from dataclasses import dataclass
import argparse

@dataclass
class ClientTimeline:
    """Client performance timeline"""
    client_id: str
    connection_time: float
    start_time: float
    end_time: float
    total_packets: int
    total_bytes: int
    avg_rate: float
    errors: int
    performance_issues: List[str]

class ClientPerformanceAnalyzer:
    """Analyzes individual client performance"""
    
    def __init__(self, results_file: str = "results/docker_test_results.json"):
        self.results_file = results_file
    
    def analyze_client_timeline(self, client_log: str, client_id: str) -> ClientTimeline:
        """Analyze a client's performance timeline"""
        lines = client_log.split('\n')
        
        timeline = ClientTimeline(
            client_id=client_id,
            connection_time=0,
            start_time=0,
            end_time=0,
            total_packets=0,
            total_bytes=0,
            avg_rate=0,
            errors=0,
            performance_issues=[]
        )
        
        # Track performance over time
        packet_milestones = []
        rate_history = []
        
        for line in lines:
            # Parse timestamps
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
            if timestamp_match:
                timestamp_str = timestamp_match.group(1)
                # Convert to seconds since start (simplified)
                timeline.connection_time = self._parse_timestamp(timestamp_str)
            
            # Track connection
            if 'connected to' in line:
                timeline.connection_time = self._parse_timestamp_from_line(line)
            
            # Track data transmission start
            if 'starting data transmission' in line:
                timeline.start_time = self._parse_timestamp_from_line(line)
            
            # Track progress milestones
            if 'packets,' in line and 'Hz' in line:
                milestone = self._parse_progress_milestone(line)
                if milestone:
                    packet_milestones.append(milestone)
                    rate_history.append(milestone['rate'])
            
            # Track final statistics
            if 'Total packets sent:' in line:
                timeline.total_packets = self._extract_number_after(line, 'Total packets sent: ')
            elif 'Total bytes sent:' in line:
                timeline.total_bytes = self._extract_number_after(line, 'Total bytes sent: ')
            elif 'Average rate:' in line:
                timeline.avg_rate = self._extract_number_after(line, 'Average rate: ')
            elif 'Errors:' in line and not 'ERROR' in line:
                timeline.errors = self._extract_number_after(line, 'Errors: ')
        
        # Analyze performance issues
        timeline.performance_issues = self._analyze_performance_issues(
            packet_milestones, rate_history, timeline
        )
        
        return timeline
    
    def _parse_timestamp_from_line(self, line: str) -> float:
        """Extract timestamp from log line"""
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
        if timestamp_match:
            return self._parse_timestamp(timestamp_match.group(1))
        return 0
    
    def _parse_timestamp(self, timestamp_str: str) -> float:
        """Parse timestamp string to seconds"""
        try:
            from datetime import datetime
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
            return dt.timestamp()
        except:
            return 0
    
    def _parse_progress_milestone(self, line: str) -> Dict[str, Any]:
        """Parse progress milestone from log line"""
        try:
            # Extract pattern: "Client client_000: 1000 packets, 4312.5 Hz"
            if 'Client client_' in line and 'packets,' in line:
                parts = line.split('Client client_')
                if len(parts) > 1:
                    after_client = parts[1].split(':')[1] if ':' in parts[1] else parts[1]
                    packet_part = after_client.strip().split(',')[0]
                    rate_part = after_client.strip().split(',')[1] if ',' in after_client else ''
                    
                    if 'packets' in packet_part and 'Hz' in rate_part:
                        packets = int(packet_part.split()[0])
                        rate = float(rate_part.split()[0])
                        return {
                            'packets': packets,
                            'rate': rate,
                            'timestamp': self._parse_timestamp_from_line(line)
                        }
        except:
            pass
        return None
    
    def _extract_number_after(self, line: str, prefix: str) -> int:
        """Extract number after a specific prefix"""
        try:
            parts = line.split(prefix)
            if len(parts) > 1:
                return int(parts[1].strip())
        except:
            pass
        return 0
    
    def _analyze_performance_issues(self, milestones: List[Dict], rates: List[float], timeline: ClientTimeline) -> List[str]:
        """Analyze performance issues from timeline data"""
        issues = []
        
        # Check for low packet count (adjusted for 15-second test)
        if timeline.total_packets > 0 and timeline.total_packets < 50000:  # Less than 50K packets for 15-second test
            issues.append(f"Low packet count: {timeline.total_packets} (expected ~120K for 15s test)")
        
        # Check for low rate (adjusted for 15-second test)
        if timeline.avg_rate > 0 and timeline.avg_rate < 2000:  # Less than 2kHz for 15-second test
            issues.append(f"Low average rate: {timeline.avg_rate:.1f} Hz (expected ~8K Hz for 15s test)")
        
        # Check for rate degradation
        if len(rates) > 5:
            early_rates = rates[:3]
            late_rates = rates[-3:]
            if len(early_rates) > 0 and len(late_rates) > 0:
                early_avg = sum(early_rates) / len(early_rates)
                late_avg = sum(late_rates) / len(late_rates)
                if late_avg < early_avg * 0.5:  # 50% degradation
                    issues.append(f"Rate degradation: {early_avg:.1f} Hz -> {late_avg:.1f} Hz")
        
        # Check for connection delays
        if timeline.start_time > 0 and timeline.connection_time > 0:
            connection_delay = timeline.start_time - timeline.connection_time
            if connection_delay > 1.0:  # More than 1 second delay
                issues.append(f"Connection delay: {connection_delay:.2f}s")
        
        # Check for errors
        if timeline.errors > 0:
            issues.append(f"Errors detected: {timeline.errors}")
        
        return issues
    
    def analyze_all_clients(self) -> Dict[str, ClientTimeline]:
        """Analyze all clients"""
        try:
            with open(self.results_file, 'r') as f:
                data = json.load(f)
            
            timelines = {}
            
            # Get server data for estimation
            server_logs = data.get('server_logs', '')
            server_packets = 0
            server_bytes = 0
            
            # Extract server statistics
            for line in server_logs.split('\n'):
                if 'Total:' in line and 'packets,' in line:
                    try:
                        parts = line.split('Total:')[1].split(',')
                        if len(parts) >= 2:
                            packet_part = parts[0].strip()
                            byte_part = parts[1].strip()
                            
                            if 'packets' in packet_part:
                                server_packets = int(packet_part.split()[0])
                            if 'bytes' in byte_part:
                                server_bytes = int(byte_part.split()[0])
                    except:
                        pass
            
            # Analyze each client
            client_count = len(data.get('client_logs', {}))
            estimated_packets = server_packets // client_count if client_count > 0 else 0
            estimated_bytes = server_bytes // client_count if client_count > 0 else 0
            
            for client_id, client_log in data.get('client_logs', {}).items():
                timeline = self.analyze_client_timeline(client_log, client_id)
                
                # If no packets detected from logs, use server estimates
                if timeline.total_packets == 0 and estimated_packets > 0:
                    timeline.total_packets = estimated_packets
                    timeline.total_bytes = estimated_bytes
                    timeline.avg_rate = estimated_packets / 15.0  # 15 second test
                    timeline.connection_status = 'connected'
                
                timelines[client_id] = timeline
            
            return timelines
            
        except Exception as e:
            print(f"Error analyzing clients: {e}")
            return {}
    
    def print_analysis(self, timelines: Dict[str, ClientTimeline]):
        """Print detailed analysis"""
        print("=" * 80)
        print("CLIENT PERFORMANCE ANALYSIS")
        print("=" * 80)
        
        # Sort clients by performance
        sorted_clients = sorted(timelines.items(), 
                              key=lambda x: x[1].total_packets, reverse=True)
        
        for client_id, timeline in sorted_clients:
            print(f"\nCLIENT: {client_id}")
            print(f"  Packets: {timeline.total_packets:,}")
            print(f"  Bytes: {timeline.total_bytes:,}")
            print(f"  Rate: {timeline.avg_rate:.1f} Hz")
            print(f"  Errors: {timeline.errors}")
            
            if timeline.performance_issues:
                print(f"  ISSUES:")
                for issue in timeline.performance_issues:
                    print(f"    - {issue}")
            else:
                print(f"  No issues detected")
        
        # Summary
        print(f"\nSUMMARY:")
        total_packets = sum(t.total_packets for t in timelines.values())
        avg_packets = total_packets / len(timelines) if timelines else 0
        print(f"  Total packets: {total_packets:,}")
        print(f"  Average per client: {avg_packets:,.0f}")
        
        # Identify underperforming clients
        underperformers = [c for c, t in timelines.items() 
                          if t.total_packets < avg_packets * 0.5]
        if underperformers:
            print(f"  Underperforming clients: {', '.join(underperformers)}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Client Performance Analyzer')
    parser.add_argument('--file', default='docker_test_results.json', 
                       help='Docker results file to analyze')
    
    args = parser.parse_args()
    
    analyzer = ClientPerformanceAnalyzer(args.file)
    timelines = analyzer.analyze_all_clients()
    
    if timelines:
        analyzer.print_analysis(timelines)
    else:
        print("No client data found")

if __name__ == '__main__':
    main()
