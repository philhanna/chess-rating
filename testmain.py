#! /usr/bin/python


from rating.chess_com.chesscom import ChessCom
from rating.fide.fide import FIDE
from rating.lichess.lichess import Lichess
from rating.uscf.uscf import USCF


if __name__ == "__main__":
    import argparse
    from rating import Main

    parser = argparse.ArgumentParser(
        description="Fetches and prints a players's chess rating from USCF, FIDE, Lichess, or Chess.com."
    )

    # Positional argument for the player's ID or name
    parser.add_argument(
        "player",
        help="The player's ID or name.",
    )

    # Create a mutually exclusive group
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-u", "--uscf", action="store_true", help="Use USCF platform")
    group.add_argument("-l", "--lichess", action="store_true", help="Use Lichess platform")
    group.add_argument("-c", "--chess", action="store_true", help="Use chess.com platform")
    group.add_argument("-f", "--fide", action="store_true", help="Use FIDE platform")


    args = parser.parse_args()

    app = None        
    player = args.player

    # Invoke the proper subclass (uscf, lichess, FIDE, or chess.com)
    if args.lichess:
        app = Lichess(player)
    elif args.chess:
        app = ChessCom(player) 
    elif args.fide:
        app = FIDE(player)
    else: # USCF is the default
        app = USCF(player)
    
    if app:
        app.run()
    
    
    
