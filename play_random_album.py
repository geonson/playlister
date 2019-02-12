import mutagen
import os
import random
from pathlib import Path
import subprocess
import re

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
print(album_choice+'\n')

album_tracks = albums[album_choice]
#for track in album_tracks:
#	print(track)

#os.remove('random_album.m3u')
#playlist_file = open('random_album.m3u', 'x')
by_track_dict = {}
track_suggestion_dict = {}
params = []
for track_file in album_tracks:
	track = mutagen.File(track_file.absolute())
	#playlist_file.write(str(track)+'\n')
	if u'TRCK' in track:
		for track_number in track[u'TRCK']:
			#print(track_number)
			actual_number = int(track_number.split('/')[0])
			#print(actual_number)
			by_track_dict[actual_number] = str(track_file)
	elif u'TPOS' in track:
		for track_number in track[u'TPOS']:
			#print(track_number)
			actual_number = int(track_number.split('/')[0])
			#print(actual_number)
			by_track_dict[actual_number] = str(track_file)
	elif u'TRACKNUMBER' in track:
		for track_number in track[u'TRACKNUMBER']:
			#print(track_number)
			actual_number = int(track_number.split('/')[0])
			#print(actual_number)
			by_track_dict[actual_number] = str(track_file)
	else:
		#could not find track number, try to figure it out
		regex = re.search('^\d+', os.path.basename(str(track_file)))
		if regex is not None:
			maybe_track_number = int(regex.group())
			track_suggestion_dict[maybe_track_number] = {'file': track_file, 'muta_file':track}

	params.append(str(track_file))

if len(track_suggestion_dict) > 0:
	print('tracks were missing numbers, are these track numbers correct? (y/n)')
	for track_num, track_dict in track_suggestion_dict.items():
		print('{0} : {1}'.format(track_num, str(track_dict['file'])))
	answer = input()
	if answer == 'y':
		for track_num, track_dict in track_suggestion_dict.items():
			if isinstance(track_dict['muta_file'], mutagen.flac.FLAC):
				track_dict['muta_file']['TRACKNUMBER'] = track_num
			if isinstance(track_dict['muta_file'], mutagen.id3.ID3FileType):
				track_dict['muta_file'].tags['TRCK'] = mutagen.id3.TRCK(encoding=mutagen.id3.Encoding.LATIN1, text=u'{0}'.format(track_num))
				print(track_dict['muta_file'].tags)
			track_dict['muta_file'].save()

if len(by_track_dict) > 0:
	params.clear()
	for track_key in sorted(by_track_dict):
		params.append(by_track_dict[track_key])
else:
	params = sorted(params)

params.insert(0, 'VLC')
#print(params)
vlc_process = subprocess.Popen(params, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
