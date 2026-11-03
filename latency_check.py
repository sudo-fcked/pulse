import time
import torch

def measure_latency(model_path="models/latenet.pt"):
    # Load the saved dictionary containing weights, config, and vocab on CPU
    checkpoint = torch.load(model_path, map_location="cpu")
    
    # TODO: Instantiate your model using the config and vocab, then load weights
    # model = YourModelClass(checkpoint['config'], checkpoint['vocab'])
    # model.load_state_dict(checkpoint['weights'])
    # model.eval()

    # TODO: Create a single dummy input tensor matching your model's expected shape
    # dummy_input = ...

    # Warm-up run (optional but recommended)
    # with torch.no_grad():
    #     _ = model(dummy_input)

    # Time a single prediction
    start_time = time.time()
    # with torch.no_grad():
    #     _ = model(dummy_input)
    end_time = time.time()

    latency_ms = (end_time - start_time) * 1000
    print(f"Latency: {latency_ms:.2f} ms")

if __name__ == "__main__":
    measure_latency()
