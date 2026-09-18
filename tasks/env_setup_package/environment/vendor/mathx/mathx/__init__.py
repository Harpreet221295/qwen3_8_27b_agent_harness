def mean(xs): return sum(xs) / len(xs)
def variance(xs):
    m = mean(xs); return sum((x - m) ** 2 for x in xs) / len(xs)
def stddev(xs): return variance(xs) ** 0.5
