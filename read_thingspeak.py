import json
import time
from urllib.parse import urlencode
from urllib.request import urlopen

from settings import required


def get_latest_reading():
    channel = int(required("THINGSPEAK_CHANNEL_ID"))
    query = urlencode({"api_key": required("THINGSPEAK_READ_API_KEY")})
    url = f"https://api.thingspeak.com/channels/{channel}/feeds/last.json?{query}"
    with urlopen(url, timeout=10) as response:
        return json.load(response)


def main():
    required("THINGSPEAK_CHANNEL_ID")
    required("THINGSPEAK_READ_API_KEY")
    while True:
        reading = get_latest_reading()
        print("Temperature:", reading.get("field1"),
              "| Light:", reading.get("field2"),
              "| Sound:", reading.get("field3"))
        time.sleep(20)


if __name__ == "__main__":
    main()
