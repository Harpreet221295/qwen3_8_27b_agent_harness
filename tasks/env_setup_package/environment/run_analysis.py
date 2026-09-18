import json
from mathx import mean, stddev

data = json.load(open("data.json"))["values"]
out = f"n={len(data)} mean={mean(data):.2f} std={stddev(data):.2f}\n"
open("output.txt", "w").write(out)
print(out, end="")
