#! /usr/bin/python

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetches and prints a players's chess rating from USCF, Lichess, or Chess.com."
    )

    # Positional argument for the player's ID or name
    parser.add_argument(
        "player",
        help="The player's USCF ID or name.",
    )

    # Optional flags for fetching ratings from Lichess or Chess.com
    parser.add_argument(
        "--lichess",
        "-l",
        action="store_true",
        help="Fetch the rating from Lichess instead of USCF.",
    )

    parser.add_argument(
        "--chess",
        "-c",
        action="store_true",
        help="Fetch the rating from Chess.com instead of USCF.",
    )

    args = parser.parse_args()
    print(args)
    
