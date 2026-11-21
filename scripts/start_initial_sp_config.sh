#!/bin/bash

cd "$(dirname "$0")/.."

export PYTHONPATH=$(pwd)

#python3 -m community_playlist.tools.configure_spotify_account
hypercorn community_playlist.tools.configure_spotify_account:app \
  -b 0.0.0.0:8080 \
  --certfile=/etc/letsencrypt/live/communityplaylist.org/cert.pem \
  --keyfile=/etc/letsencrypt/live/communityplaylist.org/privkey.pem