"""
Performance Monitoring and Testing Utilities
"""
import time
import functools
import psutil
import os
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class PerformanceMetric:
    """Performance metric data class"""
    name: str
    duration: float
    memory_before: float
    memory_after: float
    timestamp: float

class PerformanceMonitor:
    """Performance monitoring singleton"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PerformanceMonitor, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.metrics: List[PerformanceMetric] = []
            self.route_stats: Dict[str, List[float]] = defaultdict(list)
            self.cache_stats = {
                'hits': 0,
                'misses': 0,
                'total_requests': 0
            }
            self._initialized = True
    
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        self.metrics.append(metric)
        
        # Keep only last 1000 metrics to prevent memory growth
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
    
    def record_route_time(self, route: str, duration: float):
        """Record route execution time"""
        self.route_stats[route].append(duration)
        
        # Keep only last 100 entries per route
        if len(self.route_stats[route]) > 100:
            self.route_stats[route] = self.route_stats[route][-100:]
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.cache_stats['hits'] += 1
        self.cache_stats['total_requests'] += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.cache_stats['misses'] += 1
        self.cache_stats['total_requests'] += 1
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate percentage"""
        total = self.cache_stats['total_requests']
        if total == 0:
            return 0.0
        return (self.cache_stats['hits'] / total) * 100
    
    def get_route_stats(self) -> Dict[str, Dict[str, float]]:
        """Get aggregated route statistics"""
        stats = {}
        for route, times in self.route_stats.items():
            if times:
                stats[route] = {
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'request_count': len(times)
                }
        return stats
    
    def get_recent_metrics(self, limit: int = 10) -> List[PerformanceMetric]:
        """Get recent performance metrics"""
        return self.metrics[-limit:]
    
    def reset_stats(self):
        """Reset all statistics"""
        self.metrics.clear()
        self.route_stats.clear()
        self.cache_stats = {'hits': 0, 'misses': 0, 'total_requests': 0}

# Global monitor instance
monitor = PerformanceMonitor()

def performance_monitor(func_name: Optional[str] = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            # Record memory before
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Record memory after
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                
                # Record metric
                metric = PerformanceMetric(
                    name=name,
                    duration=duration,
                    memory_before=memory_before,
                    memory_after=memory_after,
                    timestamp=start_time
                )
                monitor.record_metric(metric)
                
                # Also record for route stats if it looks like a route
                if 'route' in name.lower() or any(route_indicator in name.lower() 
                                                 for route_indicator in ['index', 'watch', 'stream', 'api']):
                    monitor.record_route_time(name, duration)
        
        return wrapper
    return decorator

def flask_route_monitor(app):
    """Add performance monitoring to Flask routes"""
    
    @app.before_request
    def before_request():
        """Record request start time"""
        from flask import g
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Record request performance"""
        from flask import g, request
        
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            route_name = f"{request.method} {request.endpoint or 'unknown'}"
            monitor.record_route_time(route_name, duration)
        
        return response
    
    return app

def get_system_stats() -> Dict[str, float]:
    """Get current system performance statistics"""
    process = psutil.Process(os.getpid())
    
    return {
        'cpu_percent': psutil.cpu_percent(interval=0.1),
        'memory_mb': process.memory_info().rss / 1024 / 1024,
        'memory_percent': process.memory_percent(),
        'disk_io_read_mb': psutil.disk_io_counters().read_bytes / 1024 / 1024 if psutil.disk_io_counters() else 0,
        'disk_io_write_mb': psutil.disk_io_counters().write_bytes / 1024 / 1024 if psutil.disk_io_counters() else 0,
        'open_files': len(process.open_files()),
        'threads': process.num_threads()
    }

def performance_report() -> str:
    """Generate a comprehensive performance report"""
    route_stats = monitor.get_route_stats()
    recent_metrics = monitor.get_recent_metrics(20)
    cache_hit_rate = monitor.get_cache_hit_rate()
    system_stats = get_system_stats()
    
    report = []
    report.append("=== PERFORMANCE REPORT ===\\n")
    
    # Cache performance
    report.append(f"Cache Hit Rate: {cache_hit_rate:.1f}%")
    report.append(f"Cache Requests: {monitor.cache_stats['total_requests']}")
    report.append("")
    
    # Route performance
    report.append("Route Performance:")
    for route, stats in sorted(route_stats.items(), key=lambda x: x[1]['avg_time'], reverse=True):
        report.append(f"  {route}:")
        report.append(f"    Avg: {stats['avg_time']*1000:.1f}ms")
        report.append(f"    Min: {stats['min_time']*1000:.1f}ms") 
        report.append(f"    Max: {stats['max_time']*1000:.1f}ms")
        report.append(f"    Requests: {stats['request_count']}")
    report.append("")
    
    # System stats
    report.append("System Performance:")
    report.append(f"  CPU: {system_stats['cpu_percent']:.1f}%")
    report.append(f"  Memory: {system_stats['memory_mb']:.1f}MB ({system_stats['memory_percent']:.1f}%)")
    report.append(f"  Open Files: {system_stats['open_files']}")
    report.append(f"  Threads: {system_stats['threads']}")
    report.append("")
    
    # Recent slow operations
    slow_ops = [m for m in recent_metrics if m.duration > 0.1]  # >100ms
    if slow_ops:
        report.append("Recent Slow Operations (>100ms):")
        for op in sorted(slow_ops, key=lambda x: x.duration, reverse=True)[:10]:
            report.append(f"  {op.name}: {op.duration*1000:.1f}ms")
        report.append("")
    
    return "\\n".join(report)

def load_test_simulation(base_url: str = "http://localhost:5000", num_requests: int = 100):
    """Simple load testing simulation"""
    import requests
    import concurrent.futures
    import random
    
    def make_request(url):
        """Make a single request and return timing"""
        start = time.time()
        try:
            response = requests.get(url, timeout=10)
            end = time.time()
            return {
                'url': url,
                'status': response.status_code,
                'duration': end - start,
                'success': response.status_code == 200
            }
        except Exception as e:
            end = time.time()
            return {
                'url': url,
                'status': 0,
                'duration': end - start,
                'success': False,
                'error': str(e)
            }
    
    # Test endpoints
    endpoints = [
        "/",
        "/favorites", 
        "/tags",
        "/random",
    ]
    
    print(f"Starting load test with {num_requests} requests...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for _ in range(num_requests):
            endpoint = random.choice(endpoints[:-1])  # Exclude POST endpoint for now
            url = base_url + endpoint
            futures.append(executor.submit(make_request, url))
        
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    # Analyze results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if successful:
        avg_time = sum(r['duration'] for r in successful) / len(successful)
        min_time = min(r['duration'] for r in successful)
        max_time = max(r['duration'] for r in successful)
        
        print(f"\\nLoad Test Results:")
        print(f"  Total Requests: {len(results)}")
        print(f"  Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"  Failed: {len(failed)}")
        print(f"  Average Response Time: {avg_time*1000:.1f}ms")
        print(f"  Min Response Time: {min_time*1000:.1f}ms")
        print(f"  Max Response Time: {max_time*1000:.1f}ms")
        
        if failed:
            print(f"\\nFailures:")
            for failure in failed[:5]:  # Show first 5 failures
                print(f"  {failure['url']}: {failure.get('error', 'Unknown error')}")
    
    return results

if __name__ == "__main__":
    # Example usage
    print("Performance monitoring utilities loaded")
    print("Use performance_monitor decorator, flask_route_monitor, or load_test_simulation")
