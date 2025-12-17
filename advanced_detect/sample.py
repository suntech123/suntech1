import random

# 1. Your full list
all_names = [f"Name_{i}" for i in range(1, 273)]
n = 160

# 2. Set a Seed (The "Key" to the shuffle)
# As long as this number (42) stays the same, the selection stays the same.
SEED_NUMBER = 42 

# 3. Create a seeded random instance
rng = random.Random(SEED_NUMBER)
selected_names = rng.sample(all_names, n)

print(f"Selected {len(selected_names)} names.")
print(f"First 5: {selected_names[:5]}")
# Run this code 100 times, you will get the exact same 5 names.