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
		self.track_list.append(track)

	def find_track_numbers(self):
		track_suggestions = False
		for track in self.track_list:
			track_suggestions = track.find_actual_track_number()
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

	def __getstate__(self):
		state = {}
		state['file_object'] = self.file_object
		state['actual_track_number'] = self.actual_track_number
		state['suggested_track_number'] = self.suggested_track_number
		return state

	def __setstate__(self, state):
		self.file_object = state['file_object']
		self.muta_file = None
		self.actual_track_number = state['actual_track_number']
		self.suggested_track_number = state['suggested_track_number']

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
		return album_names

	def find_actual_track_number(self):
		if self.actual_track_number is not 0:
			#already has actual track number
			pass
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
		else:
			#could not find track number, try to figure it out
			regex = re.search('^\d+', os.path.basename(str(self.file_object)))
			if regex is not None:
				maybe_track_number = int(regex.group())
				self.suggested_track_number = maybe_track_number
				return True
		return False

	def save_suggested_track_number(self):
		if self.suggested_track_number is not None:
			if isinstance(self.get_muta_file(), mutagen.flac.FLAC):
				self.get_muta_file()['TRACKNUMBER'] = self.suggested_track_number
			if isinstance(self.get_muta_file(), mutagen.id3.ID3FileType):
				self.get_muta_file().tags['TRCK'] = mutagen.id3.TRCK(encoding=mutagen.id3.Encoding.LATIN1, text=u'{0}'.format(self.suggested_track_number))
				#print(self.get_muta_file().tags)
			self.get_muta_file().save()
			self.suggested_track_number = None

def play_album_in_vlc(album):
	album.find_track_numbers()
	album.track_list.sort(key=lambda track: str(track.file_object))
	album.track_list.sort(key=lambda track: track.actual_track_number)
	params = []
	for track in album.track_list:
		params.append(str(track.file_object))
	params.insert(0, 'VLC')
	params.insert(1, '--play-and-exit')
	vlc_process = subprocess.Popen(params, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	return vlc_process

parser = argparse.ArgumentParser()
parser.add_argument('-a', '--all', help='play all albums in a random order', action='store_true')
parser.add_argument('-r', '--reimport', help='reimport library info', action='store_true')
args = parser.parse_args()
if args.all:
	print('Playing All Albums')

all_tracks = []
all_albums = {}

if args.reimport or not os.path.isfile('library'):
	root_dir = Path('.')
	file_list = [f for f in root_dir.glob('**/*') if f.is_file()]
	for file in file_list:
		pathstring = file.absolute()
		muta_file = mutagen.File(pathstring)
		if muta_file is not None:
			track = Track(file, muta_file)
			#print(muta_file.info)
			all_tracks.append(track)
			album_names = track.get_album_names()
			for album_name in album_names:
				if album_name not in all_albums:
					all_albums[album_name] = Album(album_name)
				all_albums[album_name].add_track(track)
	library_file = open('library', 'wb')
	pickle.dump(all_albums, library_file)
	library_file.close()
else:
	library_file = open('library', 'rb')
	all_albums = pickle.load(library_file)
	library_file.close()

#print(all_albums.keys())

if args.all:
	alblum_play_list = list(all_albums.keys())
	random.shuffle(alblum_play_list)
	for chosen_album_name in alblum_play_list:
		print(chosen_album_name+'\n')
		chosen_album = all_albums[chosen_album_name]
		vlc_process = play_album_in_vlc(chosen_album)
		vlc_process.wait()
else:
	chosen_album_name = random.choice(list(all_albums.keys()))
	print(chosen_album_name+'\n')
	chosen_album = all_albums[chosen_album_name]
	vlc_process = play_album_in_vlc(chosen_album)
