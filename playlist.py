#scope user-library-modify playlist-modify-private
# 6G23TUJfaVNiHtWuscuudF
import sys
import spotipy
import spotipy.util as util
import requests
import cPickle as pickle
import datetime
import os.path
import getopt

class Song:

    def __init__(self, song):
        self.title = self.songTitle(song)
        self.artist = self.songArtist(song)
        self.artistID = self.songArtistID(song)
        self.ID = self.songID(song)
        self.album = self.songAlbum(song)
        self.albumID = self.songAlbumID(song)

    def __str__(self):
        return "Title: %s, Artist: %s, ID: %s" % (self.title, self.artist, self.ID )

    def __gt__(self, song2):
        return self.ID == song2.ID

    @staticmethod
    def songTitle(song):
        track = song['track']
        try:
            name = str(track['name'])
        except UnicodeEncodeError:
            name = track['name']
        return name

    @staticmethod
    def songID(song):
        track = song['track']
        trackId = str(track['id'])
        return trackId

    @staticmethod
    def songAlbum(song):
        track = song['track']
        albumInfo = track['album']
        try:
            name = str(albumInfo['name'])
        except UnicodeEncodeError:
            name = albumInfo['name']
        return name

    @staticmethod
    def songAlbumID(song):
        track = song['track']
        albumInfo = track['album']
        try:
            ID = str(albumInfo['id'])
        except UnicodeEncodeError:
            ID = albumInfo['id']
        return ID

    @staticmethod
    def songArtist(song):
        track = song['track']
        artistsInfo = track['artists']
        if len(artistsInfo) == 1:
            try:
                artistName = str(artistsInfo[0]['name'])
            except UnicodeEncodeError:
                artistName = artistsInfo[0]['name']
            return artistName
        else:
            artistList = []
            for artistInfo in artistsInfo:
                try:
                    artist = str(artistInfo['name'])
                    artistList.append(artist)
                except UnicodeEncodeError:
                    artist = artistInfo['name']
                    artistList.append(artist)
            return artistList

    @staticmethod
    def songArtistID(song):
        track = song['track']
        artistsInfo = track['artists']
        if len(artistsInfo) == 1:
            try:
                artistID = str(artistsInfo[0]['id'])
            except UnicodeEncodeError:
                artistID = artistsInfo[0]['id']
            return artistID
        else:
            artistIDList = []
            for artistInfo in artistsInfo:
                try:
                    artistID = str(artistInfo['id'])
                    artistIDList.append(artistID)
                except UnicodeEncodeError:
                    artistID = artistInfo['id']
                    artistIDList.append(artistID)
            return artistIDList


class Playlist:
    trackFields = 'next, items(track(name, id, artists(name,id), album(id, name)))'
    tracks = []
    cacheTime = 12

    def __init__(self,**args):
        self.username = args['username']
        if 'playlistID' in args:
            self.playlistID = args['playlistID']
            self.fle = './resources/' + self.playlistID + '.pkl'
            load =  self.loadPlaylist()
            self.loadTracks(load, self.getPlaylistSongs)
        elif 'playlistName' in args:
            self.playlistName = args['playlistName']
            self.playlistID = self.getPlaylistID(self.username, self.playlistName)
            self.fle = './resources/' + self.playlistID + '.pkl'
            print 'Playlist ID is: %s' % self.playlistID
        else:
            self.playlistID = 'SavedMusic'
            self.playListName = 'Saved Music'
            self.fle = './resources/' + self.playlistID + '.pkl'

    def __len__(self):
        return len(self.tracks)

    def getPlaylistSongs(self):
        tracks = []
        limit = 100
        offset = 0
        hasNext = True
        while hasNext:
            response = sp.user_playlist_tracks(self.username, self.playlistID, self.trackFields, limit, offset )
            hasNext = response['next']
            tracks += self.setSongs(response)
            offset += limit
        self.tracks = tracks
        self.updateTime = datetime.datetime.now()

    def loadTracks(self, load, loadMethod):
        args = sys.argv[1:]
        update = False
        for arg in args:
            if arg == '-u':
                print 'Updating %s' % self.playlistID
                loadMethod()
                update = True


        if not update:
            if load is not None:
                if self.playlistID == load.playlistID and self.username == load.username:
                    now = datetime.datetime.now()
                    if not hasattr(load,'updateTime'):
                        print 'Updating %s' % self.playlistID
                        loadMethod()
                        return

                    if load.updateTime  > now - datetime.timedelta(hours = self.cacheTime):
                        self.tracks = load.tracks
                        self.updateTime = load.updateTime
                    else:
                        print 'Updating %s' % self.playlistID
                        loadMethod()

            else:
                print 'Updating %s' % self.playlistID
                loadMethod()

    def setSongs(self,response):
        tracks = []
        allSongs = response['items']
        for song in allSongs:
            tracks.append(Song(song))
        return tracks

    def listID(tracks):
        return {tracks[i].ID for i in range(0,len(tracks)))

    def removeSongs(self):
        trackIDs = [self.tracks[i].ID for i in range(0,len(self)) ]
        if len(trackIDs) > 0 :
            generator = Playlist.chunks(trackIDs, 100)
            for tracks in generator:
                sp.user_playlist_remove_all_occurrences_of_tracks(self.username, self.playlistID, tracks)

    @staticmethod
    def addSongs(songs, username, playlists):
        listArg = type(playlists) is list
        if listArg:
            currentTracks = playlists[0].tracks
            backupTracks = playlists[1].tracks
            newTracks = []
            for song in songs:
                if not song in currentTracks and not song in backupTracks:
                    print song
                    newTracks.append(song.ID)
            if len(newTracks) > 0:
                generator = Playlist.chunks(newTracks,100)
                for tracks in generator:
                    sp.user_playlist_add_tracks(username,playlists[0].playlistID, tracks)
                    sp.user_playlist_add_tracks(username,playlists[1].playlistID, tracks)
            print 'Added %d Songs To Playlist' % len(newTracks)
            return len(newTracks)
        else:
            currentTracks = playlists.tracks
            newTracks = []
            for song in songs:
                if not song in currentTracks:
                    newTracks.append(song.ID)
            if len(newTracks) > 0:
                generator = Playlist.chunks(newTracks,100)
                for tracks in generator:
                    sp.user_playlist_add_tracks(username,playlists.playlistID, tracks)
            print 'Added %d Songs To Playlist' % len(newTracks)
            return len(newTracks)

    @staticmethod
    def trimTracks(music): # Removes all duplicate artists from music
        length = len(music)
        i = 0
        while i < length :
            unique = True
            searchTrack = music[i]
            x = i + 1
            while x < length:
                compareTrack = music[x]
                if type(compareTrack.artistID) is list:
                    increase = True
                    for artist in compareTrack.artistID:
                        if searchTrack.artistID== artist:
                            music.remove(compareTrack)
                            length = len(music)
                            unique = False
                            increase = False
                    if increase:
                        x +=1
                elif searchTrack.artistID == compareTrack.artistID:
                    music.remove(compareTrack)
                    length = len(music)
                    unique = False
                else: x += 1
            if not unique:
                music.remove(searchTrack)
                length = len(music)
            else:
                i += 1
        return music

    @staticmethod
    def getPlaylistID(username, playlistName):#
        response = sp.user_playlists(username)
        playlists = response['items']
        playlistID = []
        found = [] # Boolean list if playlist name was found
        # Checks if looking for more than one playlist
        listArg = type(playlistName) is list
        if listArg:
            for name in playlistName:
                found.append(False)
            for playlist in playlists:
                currentName = playlist['name']
                i = 0
                for name in playlistName:
                    if currentName == name:
                        found[i] = True
                        playlistID.append(playlist['id'])
                    i += 1
                if all(found):
                    break
        else:
            found.append(False)
            for playlist in playlists:
                currentName = playlist['name']
                if currentName == playlistName:
                    found[0] = True
                    playlistID = str(playlist['id'])
                    break
        i = 0
        for f in found:
            if listArg:
                if not f:
                    newPlaylist = sp.user_playlist_create(username, playlistName[i], False)
                    playlistID.append(newPlaylist['id'])
                    print "Created Playlist: %s" % playlistName[i]
            else:
                if not f:
                    newPlaylist = sp.user_playlist_create(username, playlistName, False)
                    playlistID = newPlaylist['id']
                    print "Created Playlist: %s" % playlistName
            i += 1
        return playlistID

    def loadPlaylist(self):
        directory = './resources'
        if not os.path.exists(directory):
            os.makedirs(directory)
        if os.path.isfile(self.fle):
            with open(self.fle, 'rb') as input:
                playlist = pickle.load(input)
        else: return None
        return playlist

    def savePlaylist(self):
        with open(self.fle, 'w+') as output:
            pickle.dump(self,output, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def chunks(l, n):
        """Yield successive n-sized chunks from l."""
        for i in xrange(0, len(l), n):
            yield l[i:i+n]


class SavedMusic(Playlist):

    def __init__(self, **args):
        Playlist.__init__(self, username = args['username'])
        load =  self.loadPlaylist()
        self.loadTracks(load, self.getSavedSongs)
        self.uniqueTracks = self.trimTracks(self.tracks)

    def getSavedSongs(self):
        tracks = []
        limit = 50
        offset = 0
        hasNext = True
        while hasNext is not None:
            response = sp.current_user_saved_tracks(limit, offset)
            hasNext = response['next']
            tracks += self.setSongs(response)
            offset += limit
        self.tracks = tracks
        self.updateTime = datetime.datetime.now()


def trackIDs(response): #returns a list of ids from a playlist
    allSongs = response['items']
    #print allSongs[70]
    trackIDs = []
    for song in allSongs:
        trackID = songID(song)
        trackIDs.append(trackID)
    return set(trackIDs)

def addSongs(songs, playist1, playlist2):
    currentTracks = playlist1.tracks
    backupTracks = playlist2.tracks
    newTracks = []
    for song in songs:
        if not song in currentTracks and not song in backupTracks:
            newTracks.append(song.ID)

    if len(newTracks) > 0:
        generator = chunks(newTracks,100)
        for tracks in generator:
            sp.user_playlist_add_tracks(username,playlistID1, tracks)
            sp.user_playlist_add_tracks(username,playlistID2, tracks)
    return len(newTracks)

def addUniqueMusic(playlistName):
    uniqueMusic = getUniqueMusic()
    playlistIDs = Playlist.getPlaylistID(username, playlistName)
    count = addSongs(uniqueMusic, playlistIDs[0], playlistIDs[1])
    print "Added %d Songs to %s Playlist" % (count,playList1)

scope = 'playlist-modify-private playlist-read-private user-library-modify'
playlistScope = "playlist-read-private"
playlistName = "Discovery"
playlistID = "6zQFlEHoqDHEihRaMlpYII"
clientID = '8ae602371cbf4a5db0686edc39461846'
clientSecret = '4748666c10224174bb07af8750f2a2c0'
redirectURL = 'http://localhost:8888/callback'
#ID = '2Uu7Sono1hadCjiy298ldx'
ID = '7MpBAMBCffGkjdcuzTzdbO'
backupID = '1yMx3Htp4UCBPLpwdVRyLX'
trackFields = 'next, items(track(name, id, artists(name,id), album(id, name)))'
if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    print "Usage: %s username" % (sys.argv[0],)
    sys.exit()

token = util.prompt_for_user_token(username, scope, clientID, clientSecret, redirectURL)

if token:
    sp = spotipy.Spotify(auth=token)
    #t = sp.user_playlist_tracks(username, ID, trackFields, 1, 0 )
    play = Playlist(username=username, playlistID=ID)
    saved = SavedMusic(username=username)
    backup = Playlist(username= username, playlistID = backupID)
    print Playlist.addSongs(saved.uniqueTracks, username, [play,backup])
    #print saved.tracks[0]
    play.savePlaylist()
    saved.savePlaylist()
    backup.savePlaylist()




else:
    print "Can't get token for", username