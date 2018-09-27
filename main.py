from playlist import Playlist
from playlist import SavedMusic

import util as ut
import sys
import spotipy
import os
import pickle
import requests


import spotipy.util as util
import spotipy.oauth2 as oauth2

def apiURL(newUser):
    data = {'scope': 'playlist-modify-private playlist-read-private user-library-modify user-library-read',
            'redirect_uri':'http://localhost:8888/callback',
            'response_type':'code',
            'client_id': '8ae602371cbf4a5db0686edc39461846',
            'show_dialog': newUser
            }

    r = requests.get('https://accounts.spotify.com/authorize/', params=data)
    return r.url

def browser(url):
    pass
    # driver = webdriver.Firefox()
    # driver.get(url)
    # while url[:10] == driver.current_url[:10]: time.sleep(0.2)
    # response = driver.current_url
    # driver.quit()
    # return response

# Checks if username is already found
def getUsername(username):
    directory = './resources'
    fle = directory + '/username.pkl'
    sameUser = False
    if not os.path.exists(directory):
        os.makedirs(directory)
    elif os.path.isfile(fle):
        with open(fle, 'rb') as input:
            prevUsername = pickle.load(input)
        sameUser = username == prevUsername

    pickle.dump(username, open( fle, "wb" ))

    # with open(fle, 'wb') as output:
    #     print(type(username))

    return sameUser

def getToken(outh):
    print( 'Authenticating User')
    url = apiURL(True)
    webbrowser.open_new(url)
    response = input('Enter url here: ')
    code = outh.parse_response_code(response)
    try:
        return outh.get_access_token(code)['access_token']
    except Exception as e:
        return None

def getCliIDSecret():
    codes = ut.configSectionMap("Codes")
    try:
        clientID = codes["clientid"]
    except KeyError as e:
        print("Invalid client ID ")
        sys.exit()
    try:
        clientSecret = codes["clientsecret"]
    except KeyError as e:
        print("Invalid client Secret")
        sys.exit()
    return clientID, clientSecret



sameUser = False
scope = 'playlist-modify-private playlist-read-private user-library-modify user-library-read'
clientID, clientSecret =  getCliIDSecret()
redirectURL = 'http://localhost:8888/callback'
outh = oauth2.SpotifyOAuth(clientID,clientSecret,redirectURL,scope=scope,cache_path='./resources/token')
args = sys.argv[1:]
token = None


if len(sys.argv) > 1:
    username = sys.argv[1]
    sameUser = getUsername(username)
else:
    print( "Usage: %s username" % (sys.argv[0],))
    sys.exit()

for arg in args:
    if arg == '-a':
        token = getToken(outh)
        sameUser = True


if sameUser:
    cached_token = outh.get_cached_token()
    if cached_token:
        token = cached_token['access_token']

if not token:
    token = getToken(outh)


if token:
    sp = spotipy.Spotify(auth=token)
    Playlist.getPlaylistID(username, ['Discovery', 'Backup'])
    playlistIDs = Playlist.loadIDs(username)
    if not playlistIDs:
        pass
    else:
        play = Playlist(sp=sp ,username=username, playlistID = playlistIDs['Discovery'])
        saved = SavedMusic(sp=sp, username=username)
        backup = Playlist(sp=sp, username= username, playlistID = playlistIDs['Backup'])
        #
        Playlist.addSongs(saved.uniqueTracks, username, [play,backup])
        play.savePlaylist()
        saved.savePlaylist()
        backup.savePlaylist()
else:
    print("Can't get token for", username)
