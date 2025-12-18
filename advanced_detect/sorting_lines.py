# 1. Your existing list (simulated based on your image)
# lines = [VisualLine(...), VisualLine(...)]

# 2. The Sort Command
# We round to 1 decimal place to handle slight alignment jitter
lines.sort(key=lambda l: (round(l.y0, 1), l.x0))

# 3. Print to verify
print("--- Sorted Visual Lines ---")
for line in lines:
    print(f"y={line.y0:.2f}, x={line.x0:.2f}, ori={line.orientation}")