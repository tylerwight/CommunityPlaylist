#!/bin/bash

cd "$(dirname "$0")/.."

export PYTHONPATH=$(pwd)

hypercorn community_playlist.web.CommunityPlaylist:app \
  -b 0.0.0.0:8080 \
  --certfile=/etc/letsencrypt/live/communityplaylist.org/cert.pem \
  --keyfile=/etc/letsencrypt/live/communityplaylist.org/privkey.pem