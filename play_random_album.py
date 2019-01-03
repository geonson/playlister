import mutagen
import os
import random
from pathlib import Path
import subprocess

all_tracks = []
albums = {}

root_dir = Path('.')
file_list = [f for f in root_dir.glob('**/*') if f.is_file()]

for file in file_list:
	pathstring = file.absolute()
	track = mutagen.File(pathstring)
	if track is not None:
		#print(track.info)
		all_tracks.append(track)
		#print(track)
		if u'Album' in track:
			for album_name in track[u'Album']:
				if album_name not in albums:
					albums[album_name] = list()
				albums[album_name].append(file)
		elif u'TALB' in track:
			for album_name in track[u'TALB']:
				if album_name not in albums:
					albums[album_name] = list()
				albums[album_name].append(file)

#print(albums.keys())
album_choice = random.choice(list(albums.keys()))
print(album_choice)

album_tracks = albums[album_choice]
#for track in album_tracks:
#	print(track)

#os.remove('random_album.m3u')
#playlist_file = open('random_album.m3u', 'x')
by_track_dict = {}
params = []
for track_file in album_tracks:
	track = mutagen.File(track_file.absolute())
	#playlist_file.write(str(track)+'\n')
	if u'TRCK' in track:
		for track_number in track[u'TRCK']:
			#print(track_number)
			actual_number = int(track_number.split('/')[0])
			print(actual_number)
			by_track_dict[actual_number] = str(track_file)
	elif u'TPOS' in track:
		for track_number in track[u'TPOS']:
			#print(track_number)
			actual_number = int(track_number.split('/')[0])
			print(actual_number)
			by_track_dict[actual_number] = str(track_file)
	elif u'TRACKNUMBER' in track:
		for track_number in track[u'TRACKNUMBER']:
			#print(track_number)
			actual_number = int(track_number.split('/')[0])
			print(actual_number)
			by_track_dict[actual_number] = str(track_file)
	else:
		print(track.pprint())
	params.append(str(track_file))

if len(by_track_dict) > 0:
	params.clear()
	for track_key in sorted(by_track_dict):
		params.append(by_track_dict[track_key])
else:
	params = sorted(params)

params.insert(0, 'VLC')
print(params)
vlc_process = subprocess.Popen(params)
