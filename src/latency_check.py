import time, torch
x = torch.randn(1, 48)
linear = torch.nn.Linear(48, 1)
start = time.perf_counter()
_ = linear(x)
elapsed_ms = (time.perf_counter() - start) * 1000.0
print(f"Measured single-prediction latency: {elapsed_ms:.2f} ms")
