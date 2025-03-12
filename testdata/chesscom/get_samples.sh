#!/bin/bash

# List of usernames
players=("pehanna7" "danbock" "madmsk")

# Loop through each player
for player in "${players[@]}"; do
    echo "Fetching data for $player..."

    # Fetch stats and format JSON
    curl -o temp.json "https://api.chess.com/pub/player/$player/stats" && jsonpp temp.json > "$player.json"

    # Fetch profile page
    curl -o "$player.html" "https://www.chess.com/member/$player"
done

# Remove temporary file
rm -f temp.json

