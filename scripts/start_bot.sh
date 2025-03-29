#!/bin/bash

cd "$(dirname "$0")/.."

export PYTHONPATH=$(pwd)

python3 -m community_playlist.bot.CommunityPlaylistBot
