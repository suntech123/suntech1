import torch

# 1. Check if your Beast (4090) is awake
print(f"Is CUDA available? {torch.cuda.is_available()}")
print(f"GPU Name: {torch.cuda.get_device_name(0)}")

# 2. Create a Tensor (Like a numpy array)
x = torch.rand(5, 3) 
print("CPU Tensor:\n", x)

# 3. Move it to the GPU (This is where the speed happens)
if torch.cuda.is_available():
    x = x.to("cuda")
    print("GPU Tensor:\n", x)