import sys
import os.path
import spotipy.oauth2 as oauth2
import cPickle as pickle
import requests
import spotipy
import selenium
from selenium import webdriver
from playlist import Playlist, SavedMusic, Song

def apiURL(newUser):
    data = {'scope': 'playlist-modify-private playlist-read-private user-library-modify',
            'redirect_uri':'http://localhost:8888/callback',
            'response_type':'code',
            'client_id': '8ae602371cbf4a5db0686edc39461846',
            'show_dialog': newUser
            }

    r = requests.get('https://accounts.spotify.com/authorize/', params=data)
    return r.url

def browser(url):
    print url
    driver = webdriver.Firefox()
    driver.get(url)
    while url[:10] == driver.current_url[:10]: time.sleep(0.2)
    response = driver.current_url
    driver.quit()
    return response

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
    with open(fle, 'w+') as output:
        pickle.dump(username, output, pickle.HIGHEST_PROTOCOL)
    return sameUser

def getToken(outh):
    print 'Authenticating User'
    url = apiURL(True)
    response = browser(url)
    code = outh.parse_response_code(response)
    return outh.get_access_token(code)['access_token']

sameUser = False
scope = 'playlist-modify-private playlist-read-private user-library-modify'
clientID = '8ae602371cbf4a5db0686edc39461846'
clientSecret = '4748666c10224174bb07af8750f2a2c0'
redirectURL = 'http://localhost:8888/callback'
outh = oauth2.SpotifyOAuth(clientID,clientSecret,redirectURL,scope=scope,cache_path='./resources/token')
args = sys.argv[1:]

if len(sys.argv) > 1:
    username = sys.argv[1]
    sameUser = getUsername(username)
else:
    print "Usage: %s username" % (sys.argv[0],)
    sys.exit()

for arg in args:
    if arg == '-a':
        token = getToken(outh)
        sameUser = True


if not sameUser:
    token = getToken(outh)
else:
    cached_token = outh.get_cached_token()
    if cached_token:
        token = cached_token['access_token']
    else: token = getToken(outh)

if token:
    sp = spotipy.Spotify(auth=token)
    Playlist.getPlaylistID(username, ['Discovery', 'Backup'])
    playlistIDs = Playlist.loadIDs(username)
    if not playlistIDs:
        pass
    else:
        play = Playlist(spotipy=sp,username=username, playlistID = playlistIDs['Discovery'])
        saved = SavedMusic(spotipy=sp, username=username)
        backup = Playlist(spotipy=sp, username= username, playlistID = playlistIDs['Backup'])

        Playlist.addSongs(sp ,saved.uniqueTracks, username, [play,backup])
        play.savePlaylist()
        saved.savePlaylist()
        backup.savePlaylist()
else:
    print "Can't get token for", username
