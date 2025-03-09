# chess.com implementation

# Data from chess.com is obtained using this URL:
#
# "https://api.chess.com/pub/player/{userid}/stats"
#
# A get request for that URL returns JSON that looks like this:
"""
{
  "chess_daily": {
    "last": {
      "rating": 1018,
      "date": 1741387755,
      "rd": 82
    },
    "best": {
      "rating": 1200,
      "date": 1715625334,
      "game": "https://www.chess.com/game/daily/708913025"
    },
    "record": {
      "win": 19,
      "loss": 15,
      "draw": 1,
      "time_per_move": 9703,
      "timeout_percent": 0
    }
  },
  "chess_rapid": {
    "last": {
      "rating": 970,
      "date": 1740903985,
      "rd": 43
    },
    "best": {
      "rating": 1108,
      "date": 1733977950,
      "game": "https://www.chess.com/game/live/109817472659"
    },
    "record": {
      "win": 458,
      "loss": 432,
      "draw": 41
    }
  },
  "chess_blitz": {
    "last": {
      "rating": 735,
      "date": 1739301808,
      "rd": 133
    },
    "record": {
      "win": 1,
      "loss": 5,
      "draw": 0
    }
  },
  "fide": 0,
  "tactics": {
    "highest": {
      "rating": 2349,
      "date": 1739064140
    },
    "lowest": {
      "rating": 796,
      "date": 1716251086
    }
  },
  "puzzle_rush": {
    "best": {
      "total_attempts": 41,
      "score": 38
    },
    "daily": {
      "total_attempts": 29,
      "score": 26
    }
  }
}
"""
# Output looks like this:
#
# ID=12910923,daily=1018,rapid=970,blitz=735

from .chesscom import ChessCom