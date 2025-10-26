"""
A command-line tool that detects the language of input text using the Detect Language API.
The program accepts text either as command-line arguments or via standard input,
sends it to the Detect Language API for analysis, and outputs the detected language(s)
along with confidence scores and reliability indicators.

Usage:
    1. As command-line argument: python script.py "your text here"
    2. Via standard input: echo "your text" | python script.py
    3. Interactive mode: Run the script and enter text when prompted

Requires:
    - DETECT_LANGUAGE_API_KEY environment variable to be set
    - detectlanguage package installed
"""

import json
import os
import sys
import detectlanguage
from typing import List, Dict, Any
from urllib import error, parse, request

detectlanguage.configuration.api_key = "98ae0e43407ad7a28b6ee734f520ad38"
API_URL = "https://ws.detectlanguage.com/v3/detect"


def detect_language(text: str, api_key: str) -> List[Dict[str, Any]]:
    """Call the Detect Language API and return the list of detections."""
    if not text.strip():
        raise ValueError("Input text must not be empty.")

    payload = parse.urlencode({"q": text}).encode("utf-8")
    req = request.Request(API_URL, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with request.urlopen(req) as response:
        data = response.read()

    body = json.loads(data.decode("utf-8"))

    if "error" in body and body["error"]:
        err = body["error"]
        code = err.get("code", "unknown")
        msg = err.get("message", "Unknown API error.")
        raise RuntimeError(f"Detect Language API error ({code}): {msg}")

    return body.get("data", {}).get("detections", [])


def read_text_from_stdin() -> str:
    """Read all text from stdin; return an empty string if nothing was provided."""
    if sys.stdin.isatty():
        return ""
    return sys.stdin.read().strip()


def main() -> None:
    api_key = os.getenv("DETECT_LANGUAGE_API_KEY")
    if not api_key:
        print("Missing Detect Language API key.")
        print("Set the DETECT_LANGUAGE_API_KEY environment variable and retry.")
        sys.exit(1)

    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:]).strip()
    else:
        print("Enter text to detect (Ctrl-D to submit):", file=sys.stderr)
        text = read_text_from_stdin()
        if not text:
            text = input().strip()

    if not text:
        print("No text provided. Exiting.")
        sys.exit(1)

    try:
        detections = detect_language(text, api_key)
    except ValueError as exc:
        print(f"Invalid input: {exc}")
        sys.exit(1)
    except error.HTTPError as exc:
        print(f"HTTP error from Detect Language API: {exc.code} {exc.reason}")
        sys.exit(1)
    except error.URLError as exc:
        print(f"Network error: {exc.reason}")
        sys.exit(1)
    except RuntimeError as exc:
        print(str(exc))
        sys.exit(1)

    if not detections:
        print("No detections returned.")
        return

    print("Detected languages:")
    for idx, detection in enumerate(detections, start=1):
        language = detection.get("language", "?")
        confidence = detection.get("confidence", "n/a")
        reliable = detection.get("isReliable")
        reliable_str = "yes" if reliable else "no"
        print(f"{idx}. language={language} confidence={confidence} reliable={reliable_str}")


if __name__ == "__main__":
    main()

