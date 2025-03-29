import re

def album_to_tracks(album_ids, spotify_obj):
    result1 = []
    final_result = []
    for ids in album_ids:
        result1.append(spotify_obj.album_tracks(f'{ids}'))
    for item in result1:
        for x in item['items']:
            final_result.append(x['uri'])
    return final_result

def URIconverter(inp):
    if re.search("/track/", inp):
        processed = inp.split('track/')
        uri = "spotify:track:" + processed[-1][0:22]
        return uri
    elif re.search("/album/", inp):
        processed = inp.split('album/')
        uri = "spotify:album:"+processed[-1][0:22]
        return uri
    elif re.search(":playlist:", inp):
        processed = inp.split('playlist:')
        url = "https://open.spotify.com/playlist/" + processed[-1][0:22]
        return url
    
def GetPlaylistID(username, playname, spotify_obj):
    playid = ''
    playlists = spotify_obj.user_playlists(username)
    for playlist in playlists['items']:  
        if playlist['name'] == playname:  
            playid = playlist['id']
    return playid