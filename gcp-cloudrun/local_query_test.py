import json
import sys
from pathlib import Path

import requests


def main():
    if len(sys.argv) != 3:
        print("Usage: python local_query_test.py http://localhost:8080/query-file path/to/image.jpg", file=sys.stderr)
        raise SystemExit(2)

    url = sys.argv[1]
    image_path = Path(sys.argv[2])
    response = requests.post(
        url,
        data=image_path.read_bytes(),
        headers={"Content-Type": "image/jpeg"},
        timeout=120,
    )
    print("status:", response.status_code)
    try:
        print(json.dumps(response.json(), indent=2))
    except ValueError:
        print(response.text)
    response.raise_for_status()


if __name__ == "__main__":
    main()

