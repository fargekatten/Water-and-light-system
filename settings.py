import os


def required(name):
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("YOUR_"):
        raise ValueError(f"Sett miljøvariabelen {name}; se .env.example og README.md")
    return value
