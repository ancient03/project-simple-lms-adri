import requests
import time

BASE_URL = "http://localhost:8000/api/v1"
ITERATIONS = 100


def benchmark_endpoint(url, label):
    """Mengukur rata-rata response time sebuah endpoint."""
    times = []

    for i in range(ITERATIONS):
        start = time.time()
        response = requests.get(url)
        elapsed = (time.time() - start) * 1000  # Konversi ke ms
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"\n{label}")
    print(f"  Rata-rata: {avg_time:.2f} ms")
    print(f"  Minimum  : {min_time:.2f} ms")
    print(f"  Maksimum : {max_time:.2f} ms")

    return avg_time


if __name__ == "__main__":
    print("=" * 50)
    print("BENCHMARK: Simple LMS API Performance")
    print("=" * 50)

    avg_courses = benchmark_endpoint(f"{BASE_URL}/courses/", "GET /courses/")
    avg_detail = benchmark_endpoint(f"{BASE_URL}/courses/1", "GET /courses/1/")
