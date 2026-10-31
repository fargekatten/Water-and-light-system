import json
import time
from urllib.request import urlopen


)

while True:
    with urlopen(url, timeout=10) as response:
        reading = json.load(response)

    print(
        "Temperature:", reading.get("field1"),
        "| Light:", reading.get("field2"),
        "| Sound:", reading.get("field3")
    )

    time.sleep(20)