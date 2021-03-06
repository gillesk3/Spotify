import sys
import spotipy
import spotipy.util as util
import spotipy.oauth2 as oauth2
import pickle
import datetime
import getopt
import json
import os

import time

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
    directory = './resources/'

    def __init__(self,**args):
        self.username = args['username']
        self.sp = args['sp']
        if 'playlistID' in args:
            self.playlistID = args['playlistID']
            self.fle = self.directory + self.playlistID + '.pkl'
            load =  self.loadPlaylist()
            self.loadTracks(load, self.getPlaylistSongs)
        elif 'playlistName' in args:
            self.playlistName = args['playlistName']
            self.playlistID = self.getPlaylistID(self.username, self.playlistName)
            self.fle = self.directory + self.playlistID + '.pkl'
            print('Playlist ID is: %s' % self.playlistID)
        else:
            self.playlistID = 'SavedMusic'
            self.playListName = 'Saved Music'
            self.fle = self.directory + self.playlistID + '.pkl'

    def __len__(self):
        return len(self.tracks)

    # Gets list of songs in playlist, adds it to self.tracks and updates self.updaeTime
    def getPlaylistSongs(self):
        tracks = []
        limit = 100
        offset = 0
        hasNext = True
        while hasNext:
            response = self.sp.user_playlist_tracks(self.username, self.playlistID, self.trackFields, limit, offset )
            hasNext = response['next']
            tracks += self.setSongs(response)
            offset += limit
        self.tracks = tracks
        self.updateTime = datetime.datetime.now()

    #  Loads the tracks in the playlist by either checking with spotify api or loading previously cached playlist
    def loadTracks(self, load, loadMethod):
        args = sys.argv[1:]
        update = False
        for arg in args:
            if arg == '-u':
                print( 'Updating because i was told to %s' % self.playlistID)
                loadMethod()
                update = True


        if not update:
            print( 'Updating %s' % self.playlistID)

            if load is not None:
                if self.playlistID == load.playlistID and self.username == load.username:
                    now = datetime.datetime.now()
                    if not hasattr(load,'updateTime'):
                        loadMethod()
                        return

                    if load.updateTime  > now - datetime.timedelta(hours = self.cacheTime):
                        self.tracks = load.tracks
                        self.updateTime = load.updateTime
                    else:
                        loadMethod()

            else:
                loadMethod()

    # Puts the songs from the spotify query in a tracks list
    def setSongs(self,response):
        tracks = []
        allSongs = response['items']
        for song in allSongs:
            tracks.append(Song(song))
        return tracks

    # List all the ids of the tracks
    @staticmethod
    def listID(tracks):
        return [tracks[i].ID for i in range(0,len(tracks))]

    # Removes all songs given from the playlist
    def removeSongs(self, songs):
        trackIDs = [songs[i].ID for i in range(0,len(self)) ]
        if len(trackIDs) > 0 :
            generator = Playlist.chunks(trackIDs, 100)
            for tracks in generator:
                self.sp.user_playlist_remove_all_occurrences_of_tracks(self.username, self.playlistID, tracks)
        self.loadTracks(None, self.getPlaylistSongs)

    #  Adds all songs to two playlist, second playlist is to keep a backup so as not to readd songs the user removed
    # @staticmethod
    def addSongs(sp,songs, username, playlists):
        listArg = type(playlists) is list
        position = 0
        if listArg:
            currentTracks = Playlist.listID(playlists[0].tracks)
            backupTracks = Playlist.listID(playlists[1].tracks)
            newTracks = []
            for song in songs:
                if not song.ID in currentTracks and not song.ID in backupTracks:
                    newTracks.append(song.ID)
            if len(newTracks) > 0:
                generator = Playlist.chunks(newTracks,100)
                for tracks in generator:
                    sp.user_playlist_add_tracks(username,playlists[0].playlistID, tracks, position)
                    sp.user_playlist_add_tracks(username,playlists[1].playlistID, tracks, position)
            for playlist in playlists:
                playlist.getPlaylistSongs();
            print( 'Added %d Songs To Playlist' % len(newTracks) )
            return len(newTracks)
        else:
            currentTracks =  Playlist.listID(playlists.tracks)
            newTracks = []
            for song in songs:
                if not song.ID in currentTracks:
                    newTracks.append(song.ID)
            if len(newTracks) > 0:
                generator = Playlist.chunks(newTracks,100)
                for tracks in generator:
                    self.sp.user_playlist_add_tracks(username,playlists.playlistID, tracks, position)
            playlists.getPlaylistSongs();
            print( 'Added %d Songs To Playlist' % len(newTracks) )
            return len(newTracks)

    @staticmethod
    def trimTracks(songs): # Removes all duplicate artists from songs
        length = len(songs)
        i = 0
        while i < length :
            unique = True
            searchTrack = songs[i]
            x = i + 1
            while x < length:
                compareTrack = songs[x]
                if type(compareTrack.artistID) is list:
                    increase = True
                    for artist in compareTrack.artistID:
                        if searchTrack.artistID== artist:
                            songs.remove(compareTrack)
                            length = len(songs)
                            unique = False
                            increase = False
                    if increase:
                        x +=1
                elif searchTrack.artistID == compareTrack.artistID:
                    songs.remove(compareTrack)
                    length = len(songs)
                    unique = False
                else: x += 1
            if not unique:
                songs.remove(searchTrack)
                length = len(songs)
            else:
                i += 1
        return songs

    @staticmethod
    def getPlaylistID(sp,username, playlistName):
        playlistIDs = Playlist.loadIDs(username)
        if playlistIDs:
            if type(playlistName) is list:
                playlistID = []
                fAll = []
                for name in playlistName:
                    if name in playlistIDs:
                        fAll.append(True)
                        playlistID.append(playlistIDs[name])
                    else: fAll.append(False)
                if all(fAll):
                    return playlistIDs

            else :
                if playlistName in playlistIDs:
                    return playlistIDs[playlistName]

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
                    print( "Created Playlist: %s" % playlistName[i])
            else:
                if not f:
                    newPlaylist = sp.user_playlist_create(username, playlistName, False)
                    playlistID = newPlaylist['id']
                    print ("Created Playlist: %s" % playlistName)
            i += 1
        if type(playlistID) is list:
            i = 0
            for ID in playlistID:
                Playlist.saveIDs(username, {playlistName[i]:ID})
                i +=1
        else: Playlist.saveIDs(username, {playlistName: playlistID})
        return playlistID

    @staticmethod
    def loadIDs(username):

        fle = Playlist.directory + '/%sIDs.pkl' % username
        if not os.path.exists(Playlist.directory):
            os.makedirs(Playlist.directory)
            return False
        elif os.path.isfile(fle):
            with open(fle, 'rb') as input:
                playlistIDs = pickle.load(input)
            return playlistIDs
        else: return False

    @staticmethod
    def saveIDs(username, playlistIDs):

        fle = Playlist.directory + '/%sIDs.pkl' % username
        temp = None
        if not os.path.exists(Playlist.directory):
            os.makedirs(Playlist.directory)
        if os.path.isfile(fle):
            with open(fle, 'rb') as input:
                temp = pickle.load(input)
        if type(temp) is dict:
            temp.update(playlistIDs)
            playlistIDs = temp
        with open(fle, 'wb') as output:
            pickle.dump(playlistIDs, output, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def removeIDs(username, playlistName):

        fle = Playlist.directory + '/%sIDs.pkl' % username
        if not os.path.isfile(fle):
            return False
        if type(playlistName) is list:
            playlists = None
            with open(fle, 'rb') as input:
                playlists = pickle.load(input)
            for name in playlistName:
                if name in playlists:
                    del playlists[name]
            with open(fle, 'wb') as output:
                pickle.dump(playlists, output, pickle.HIGHEST_PROTOCOL)
        else:
            playlists = None
            with open(fle, 'rb') as input:
                playlists = pickle.load(input)

            if playlistName in playlists:
                del playlists[playlistName]
            with open(fle, 'wb') as output:
                pickle.dump(playlists, output, pickle.HIGHEST_PROTOCOL)

    # Loads saved playlist from resources
    def loadPlaylist(self):

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        if os.path.isfile(self.fle):
            with open(self.fle, 'rb') as input:
                playlist = pickle.load(input)
        else: return None
        return playlist

    def savePlaylist(self):
        with open(self.fle, 'wb') as output:
            pickle.dump(self,output, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def chunks(l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i+n]

# Saved music for the user
class SavedMusic(Playlist):

    def __init__(self, **args):
        Playlist.__init__(self,sp=args['sp'],  username = args['username'])
        load =  self.loadPlaylist()
        self.loadTracks(load, self.getSavedSongs)
        self.uniqueTracks = self.trimTracks(self.tracks)

    def getSavedSongs(self):
        tracks = []
        limit = 50
        offset = 0
        hasNext = True
        while hasNext is not None:
            response = self.sp.current_user_saved_tracks(limit, offset)
            hasNext = response['next']
            tracks += self.setSongs(response)
            offset += limit
        self.tracks = tracks
        self.updateTime = datetime.datetime.now()
