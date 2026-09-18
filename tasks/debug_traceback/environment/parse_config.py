import sys


def parse(path):
    sections = {}
    current = None
    for raw in open(path):
        line = raw.strip()
        if not line or line[0] in "#;":
            continue
        if line.startswith("["):
            current = line[1:line.index("]")]
            sections[current] = {}
        else:
            key, value = line.split("=")
            sections[current][key.strip()] = value.strip()
    return sections


def main():
    for name, kv in parse(sys.argv[1]).items():
        print(f"[{name}] " + " ".join(f"{k}={v}" for k, v in kv.items()))


if __name__ == "__main__":
    main()
