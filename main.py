#!/usr/bin/env python3
"""Entry point: python main.py --mode text|voice"""

import argparse

from jarvis.assistant import Assistant


def main() -> None:
    parser = argparse.ArgumentParser(description="Run your Jarvis assistant.")
    parser.add_argument(
        "--mode",
        choices=["text", "voice"],
        default="text",
        help="text: type to chat. voice: press Enter then speak.",
    )
    args = parser.parse_args()

    assistant = Assistant()
    if args.mode == "voice":
        assistant.run_voice_loop()
    else:
        assistant.run_text_loop()


if __name__ == "__main__":
    main()
