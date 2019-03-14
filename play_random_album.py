import mutagen
import os
import random
from pathlib import Path
import subprocess
import re
import argparse
import pickle

class Album:
	def __init__(self, name):
		self.name  = name
		self.track_list = []

	def add_track(self, track):
		already_has = False
		for existing_track in self.track_list:
			if str(existing_track.file_object) == str(track.file_object):
				already_has = True
				break
		if not already_has:
			self.track_list.append(track)

	def find_track_numbers(self):
		track_suggestions = False
		for track in self.track_list:
			if track.suggested_track_number is not None:
				track_suggestions = True
				break
		if track_suggestions:
			print('tracks were missing numbers, are these track numbers correct? (y/n)')
			for track in self.track_list:
				if track.suggested_track_number is not None:
					print('{0} : {1}'.format(track.suggested_track_number, str(track.file_object)))
			answer = input()
			if answer == 'y':
				for track in chosen_album.track_list:
					track.save_suggested_track_number()

class Track:
	def __init__(self, file_object, muta_file):
		self.file_object = file_object
		self.muta_file = muta_file
		self.actual_track_number = 0
		self.suggested_track_number = None
		if u'TRCK' in self.get_muta_file():
			for track_number in self.get_muta_file()[u'TRCK']:
				actual_number = int(track_number.split('/')[0])
				self.actual_track_number = actual_number
		elif u'TPOS' in self.get_muta_file():
			for track_number in self.get_muta_file()[u'TPOS']:
				actual_number = int(track_number.split('/')[0])
				self.actual_track_number = actual_number
		elif u'TRACKNUMBER' in self.get_muta_file():
			for track_number in self.get_muta_file()[u'TRACKNUMBER']:
				actual_number = int(track_number.split('/')[0])
				self.actual_track_number = actual_number
		elif u'WM/TrackNumber' in self.get_muta_file():
			for track_number in self.get_muta_file()[u'WM/TrackNumber']:
				actual_number = int(track_number.value.split('/')[0])
				self.actual_track_number = actual_number
		else:
			#could not find track number, try to figure it out
			regex = re.search('^\d+', os.path.basename(str(self.file_object)))
			if regex is not None:
				maybe_track_number = int(regex.group())
				self.suggested_track_number = maybe_track_number
		album_names = self.get_album_names()
		if len(album_names) > 0:
			self.album_name = album_names[0]
		else:
			self.album_name = ''
		#TODO: fill these in from muta file
		self.artist = None
		self.title = None

	def __getstate__(self):
		state = {}
		state['file_object'] = self.file_object
		state['actual_track_number'] = self.actual_track_number
		state['suggested_track_number'] = self.suggested_track_number
		state['album_name'] = self.album_name
		state['artist'] = self.artist
		state['title'] = self.title
		return state

	def __setstate__(self, state):
		self.file_object = state['file_object']
		self.muta_file = None
		self.actual_track_number = state['actual_track_number']
		self.suggested_track_number = state['suggested_track_number']
		self.album_name = state['album_name']
		self.artist = state['artist']
		self.title = state['title']

	def get_muta_file(self):
		if self.muta_file is None:
			self.muta_file = mutagen.File(self.file_object.absolute())
		return self.muta_file

	def get_album_names(self):
		album_names = []
		if u'Album' in self.get_muta_file():
			for album_name in self.get_muta_file()[u'Album']:
				album_names.append(album_name)
		elif u'TALB' in self.get_muta_file():
			for album_name in self.get_muta_file()[u'TALB']:
				album_names.append(album_name)
		elif u'WM/AlbumTitle' in self.get_muta_file():
			for album_name in self.get_muta_file()[u'WM/AlbumTitle']:
				album_names.append(album_name.value)
		return album_names

	def get_artist(self):
		if isinstance(self.get_muta_file(), mutagen.flac.FLAC):
			return self.get_muta_file()['TRACKNUMBER']
		if isinstance(self.get_muta_file(), mutagen.id3.ID3FileType):
			return self.get_muta_file().tags['TRCK']
		if isinstance(self.get_muta_file(), mutagen.asf.ASF):
			return self.get_muta_file().tags['WM/']

	def save_suggested_track_number(self):
		if self.suggested_track_number is not None:
			if isinstance(self.get_muta_file(), mutagen.flac.FLAC):
				self.get_muta_file()['TRACKNUMBER'] = self.suggested_track_number
			if isinstance(self.get_muta_file(), mutagen.id3.ID3FileType):
				self.get_muta_file().tags['TRCK'] = mutagen.id3.TRCK(encoding=mutagen.id3.Encoding.LATIN1, text=u'{0}'.format(self.suggested_track_number))
			if isinstance(self.get_muta_file(), mutagen.asf.ASF):
				self.get_muta_file().tags['WM/TrackNumber'] = mutagen.asf.ASFUnicodeAttribute(u'{0}'.format(self.suggested_track_number))
			self.get_muta_file().save()
			self.actual_track_number = self.suggested_track_number
			self.suggested_track_number = None

def play_tracks_in_vlc(track_list):
	params = []
	for track in track_list:
		params.append(str(track.file_object))
	params.insert(0, 'VLC')
	params.insert(1, '--play-and-exit')
	vlc_process = subprocess.Popen(params, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	return vlc_process

def validpathtype(arg):
    if os.path.isdir(arg):
        return arg
    else:
        raise argparse.ArgumentTypeError('Invalid path specification')

#intended usage
#playlister [--version] [--help | -h] [--lib=<library-file-path>] <command> [<args>]
#playlister play [--single -s] [[album | artist | track-number | track-name] [random]]...
#playlister import [-r | --reimport] <path>
#playlister tag [album] [artist] [track-number] [track-name]

parser = argparse.ArgumentParser()
parser.add_argument('--version', action='version', version='playlister 1.0')
parser.add_argument('--lib', help='location of library file')

subparsers = parser.add_subparsers(dest='command', metavar='command', help='sub-command help')
subparsers.required = True

parser_play = subparsers.add_parser('play', help='play some files')
parser_play.add_argument('-a', '--all', help='play all items', action='store_true')
parser_play.add_argument('aspect', nargs='+', choices=['album', 'artist', 'track', 'title', 'filename', 'album-random', 'artist-random', 'track-random', 'title-random', 'filename-random'])

parser_import = subparsers.add_parser('import', help='import additional files to library')
parser_import.add_argument('-r', '--reimport', help='reimport files exsting in library', action='store_true')
parser_import.add_argument('path', type=validpathtype)

parser_tag = subparsers.add_parser('tag', help="search library and attempt to fill missing tag info")
parser_tag.add_argument('field', choices=['album', 'artist', 'track', 'title'], nargs='+')

args = parser.parse_args()

#print(args)

library_filename = 'library'
if args.lib is not None and os.path.isfile(args.lib):
	library_filename = args.lib

tracks_by_filename = {}
albums_by_name = {}

if os.path.isfile(library_filename):
	library_file = open(library_filename, 'rb')
	tracks_by_filename = pickle.load(library_file)
	albums_by_name = pickle.load(library_file)
	library_file.close()

salt = random.randint(0, 999999999)

def sort_track_by_aspects(track):
	prop_list = []
	for aspect in args.aspect:
		if aspect.startswith('album'):
			prop = track.album_name
		elif aspect.startswith('artist'):
			prop = track.artist
		elif aspect.startswith('track'):
			prop = str(track.actual_track_number)
		elif aspect.startswith('title'):
			prop = track.title
		if aspect.endswith('random'):
			random.seed(prop+str(salt))
			prop_list.append(random.randint(0, 999999999))
		else:
			prop_list.append(prop)
	return prop_list

if args.command == 'play':
	play_list = list(tracks_by_filename.values())
	play_list.sort(key=lambda track: str(track.file_object))
	play_list.sort(key = sort_track_by_aspects)

	#for track in play_list:
		#print (track.album_name +'-'+str(track.actual_track_number))

	i = 0
	current_first_prop = None
	group_end = 0
	while (args.all or group_end == 0) and i < len(play_list):
		track = play_list[i]
		if args.aspect[0].startswith('album'):
			prop = track.album_name
		elif args.aspect[0].startswith('artist'):
			prop = track.artist
		elif args.aspect[0].startswith('track'):
			prop = track.actual_track_number
		elif args.aspect[0].startswith('title'):
			prop = track.title
		if current_first_prop != prop:
			if i > 0:
				group_end = i
				print('\nPlaying {0}\n{1}\n'.format(args.aspect[0], current_first_prop))
				vlc_process = play_tracks_in_vlc(play_list[group_start:group_end])
				if args.all and i+1 < len(play_list):
					vlc_process.wait()
			group_start = i
			current_first_prop = prop
		i = i+1

elif args.command == 'import':
	library_changed = False
	root_dir = Path(args.path)
	file_list = [f for f in root_dir.glob('**/*') if f.is_file()]
	for file in file_list:
		if args.reimport or str(file) not in tracks_by_filename:
			muta_file = mutagen.File(file.absolute())
			if muta_file is not None:
				print('importing track to library '+str(file))
				#print(muta_file)
				track = Track(file, muta_file)
				tracks_by_filename[str(file)] = track
				album_names = track.get_album_names()
				for album_name in album_names:
					if album_name not in albums_by_name:
						albums_by_name[album_name] = Album(album_name)
					albums_by_name[album_name].add_track(track)
				library_changed = True

	if library_changed:
		library_file = open(library_filename, 'wb')
		pickle.dump(tracks_by_filename, library_file)
		pickle.dump(albums_by_name, library_file)
		library_file.close()

elif args.command == 'tag':
	pass
