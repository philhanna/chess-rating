#! /usr/bin/python
import argparse
from rating.chesscom import ChessCom
from rating.config_loader import ConfigLoader
from rating.fide import FIDE
from rating.lichess import Lichess
from rating.uscf import USCF

# Load the configuration so that we can supply a default username
loader = ConfigLoader()
config = loader.config

parser = argparse.ArgumentParser(
    description="Fetches and prints a players's chess rating from USCF, FIDE, Lichess, or Chess.com."
)

# Positional argument for the player's ID or name
parser.add_argument("player", nargs="?", default=None, help="The player's ID or name.")

# JSON option
parser.add_argument("-j", "--json", action="store_true",
                    help="Create JSON output")

# Create a mutually exclusive group
group = parser.add_mutually_exclusive_group()
group.add_argument("-u", "--uscf", action="store_true",
                    help="Use USCF platform")
group.add_argument("-l", "--lichess", action="store_true",
                    help="Use Lichess platform")
group.add_argument("-c", "--chess", action="store_true",
                    help="Use chess.com platform")
group.add_argument("-f", "--fide", action="store_true",
                    help="Use FIDE platform")

args = parser.parse_args()

app = None

# Invoke the proper subclass (uscf, lichess, FIDE, or chess.com)
if args.lichess:
    player = args.player or config["lichess"]["defaultUser"]   
    app = Lichess(player)
elif args.chess:
    player = args.player or config["Chess"]["defaultUser"]   
    app = ChessCom(player)
elif args.fide:
    player = args.player or config["FIDE"]["defaultUser"]
    app = FIDE(player)
else:  # USCF is the default
    player = args.player or config["USCF"]["defaultUser"]   
    app = USCF(player)

if app:
    if args.json:
        app.json = True
    app.run()
