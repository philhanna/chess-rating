#! /usr/bin/python
import argparse
import json

from rating.adapters.uscf import USCF
from rating.adapters.lichess import Lichess
from rating.adapters.chesscom import ChessCom
from rating.adapters.fide import FIDE
from rating.adapters.requests_http import RequestsHttpAdapter
from rating.config_loader import ConfigLoader


def _to_json(s: str) -> str:
    d = {}
    for part in s.split("|"):
        part = part.replace('"', '')
        k, v = part.split("=")
        d[k] = v
    return json.dumps(d, indent=4)


loader = ConfigLoader()
config = loader.config

parser = argparse.ArgumentParser(
    description="Fetches and prints a players's chess rating from USCF, FIDE, Lichess, or Chess.com."
)
parser.add_argument("player", nargs="?", default=None, help="The player's ID or name.")
parser.add_argument("-j", "--json", action="store_true", help="Create JSON output")

group = parser.add_mutually_exclusive_group()
group.add_argument("-u", "--uscf", action="store_true", help="Use USCF platform")
group.add_argument("-l", "--lichess", action="store_true", help="Use Lichess platform")
group.add_argument("-c", "--chess", action="store_true", help="Use chess.com platform")
group.add_argument("-f", "--fide", action="store_true", help="Use FIDE platform")

args = parser.parse_args()

http_client = RequestsHttpAdapter()

if args.lichess:
    player = args.player or config["lichess"]["defaultUser"]
    app = Lichess(player, http_client)
elif args.chess:
    player = args.player or config["Chess"]["defaultUser"]
    app = ChessCom(player, http_client)
elif args.fide:
    player = args.player or config["FIDE"]["defaultUser"]
    app = FIDE(player, http_client)
else:  # USCF is the default
    player = args.player or config["USCF"]["defaultUser"]
    app = USCF(player, http_client)

output = app.fetch()
if not output:
    print(f'No ratings found for "{player}"')
else:
    if args.json:
        output = _to_json(output)
    print(output)
