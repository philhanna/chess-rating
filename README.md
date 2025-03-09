# Chess rating

A Python command-line tool that retrieves and prints the chess rating of a person from the specified ratings platform.

## How to call
```
usage: chess_rating.py [-h] [-u | -l | -c | -f] player

Fetches and prints a players's chess rating from USCF, FIDE, Lichess, or Chess.com.

positional arguments:
  player         The player's ID or name.

options:
  -h, --help     show this help message and exit
  -u, --uscf     Use USCF platform
  -l, --lichess  Use Lichess platform
  -c, --chess    Use chess.com platform
  -f, --fide     Use FIDE platform
```
