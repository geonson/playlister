import mutagen
import os
import random
from pathlib import Path
import subprocess
import re
import argparse
import pickle
import platform

class Track:
    def __init__(self, file_object, muta_file):
        self.file_object = file_object
        self.muta_file = muta_file
        self.artist = ''
        self.title = ''
        self.album = ''
        self.track_number = 0
        self.number_of_plays = 0
        track_number = None
        if isinstance(self.muta_file, mutagen.flac.FLAC):
            self.artist = self.muta_file.tags['ARTIST'][0]
            self.title = self.muta_file.tags['TITLE'][0]
            self.album = self.muta_file.tags['Album'][0]
            track_number = self.muta_file.tags['TRACKNUMBER'][0]

        elif isinstance(self.muta_file, mutagen.id3.ID3FileType):
            if self.muta_file.tags is not None:
                if 'TPE1' in self.muta_file.tags:
                    self.artist = self.muta_file.tags['TPE1'][0]
                elif 'TPE2' in self.muta_file.tags:
                    self.artist = self.muta_file.tags['TPE2'][0]
                elif 'TCOM' in self.muta_file.tags:
                    self.artist = self.muta_file.tags['TCOM'][0]

                if 'TIT2' in self.muta_file.tags:
                    self.title = self.muta_file.tags['TIT2'][0]

                if 'TALB' in self.muta_file.tags:
                    self.album = self.muta_file.tags['TALB'][0]

                if 'TRCK' in self.muta_file.tags:
                    track_number = self.muta_file.tags['TRCK'][0]
                elif 'TPOS' in self.muta_file.tags:
                    track_number = self.muta_file.tags['TPOS'][0]

        elif isinstance(self.muta_file, mutagen.asf.ASF):
            self.artist = self.muta_file.tags['Author'][0].value
            self.title = self.muta_file.tags['Title'][0].value
            self.album = self.muta_file.tags['WM/AlbumTitle'][0].value
            track_number = self.muta_file.tags['WM/TrackNumber'][0].value

        else:
            print('tag parsing not yet supported for type {0}'.format(self.muta_file.__class__.__name__))

        if track_number is not None and isinstance(track_number, str):
            try:
                self.track_number = int(track_number.split('/')[0])
            except ValueError:
                print('Error reading track number from file {0}'.format(str(self.file_object)))

    def __getstate__(self):
        state = {}
        state['file_object'] = self.file_object
        state['track_number'] = self.track_number
        state['album'] = self.album
        state['artist'] = self.artist
        state['title'] = self.title
        state['number_of_plays'] = self.number_of_plays
        return state

    def __setstate__(self, state):
        self.file_object = state['file_object']
        self.muta_file = None
        self.track_number = state['track_number']
        self.album = state['album']
        self.artist = state['artist']
        self.title = state['title']
        if 'number_of_plays' in state:
            self.number_of_plays = state['number_of_plays']
        else:
            self.number_of_plays = 0

    def save_new_track_number(self, track_number):
        if self.muta_file is None:
            self.muta_file = mutagen.File(self.file_object.absolute())
        if isinstance(self.muta_file, mutagen.flac.FLAC):
            self.muta_file['TRACKNUMBER'] = track_number
        if isinstance(self.muta_file, mutagen.id3.ID3FileType):
            self.muta_file.tags['TRCK'] = mutagen.id3.TRCK(encoding=mutagen.id3.Encoding.LATIN1, text=u'{0}'.format(track_number))
        if isinstance(self.muta_file, mutagen.asf.ASF):
            self.muta_file.tags['WM/TrackNumber'] = mutagen.asf.ASFUnicodeAttribute(u'{0}'.format(track_number))
        self.muta_file.save()
        self.track_number = track_number

    def __eq__(self, other):
        if isinstance(other, Track):
            return str(self.file_object) == str(other.file_object)
        return False

def validpathtype(arg):
    if os.path.isdir(arg):
        return arg
    else:
        raise argparse.ArgumentTypeError('Invalid path specification')

parser = argparse.ArgumentParser()
parser.add_argument('--version', action='version', version='playlister 1.0')
parser.add_argument('--lib', help='location of library file')

subparsers = parser.add_subparsers(dest='command', metavar='command', help='sub-command help')
subparsers.required = True

parser_play = subparsers.add_parser('play', help='play some files')
parser_play.add_argument('-a', '--all', help='play all items', action='store_true')
parser_play.add_argument('-t', '--test', help='test mode - print playlist only', action='store_true')
parser_play.add_argument('--where', help='track condition e.g. "artist==\'House Boat\'"')
parser_play.add_argument('--group_by', help='aspect to create play groups by')
parser_play.add_argument('order', nargs='+', help='aspect1 [asc|desc|random], aspect2 [asc|desc|random], ...')

parser_import = subparsers.add_parser('import', help='import additional files to library')
parser_import.add_argument('-r', '--reimport', help='reimport files exsting in library', action='store_true')
parser_import.add_argument('path', type=validpathtype)

parser_tag = subparsers.add_parser('audit', help="search library and attempt to find incorrect tag info")
parser_tag.add_argument('field', choices=['album', 'artist', 'track', 'title', 'type'], nargs='+')

args = parser.parse_args()

#print(args)

library_filename = 'library'
if args.lib is not None:
    library_filename = args.lib

tracks_by_filename = {}

if os.path.isfile(library_filename):
    library_file = open(library_filename, 'rb')
    tracks_by_filename = pickle.load(library_file)
    library_file.close()

salt = random.randint(0, 999999999)

if args.command == 'play':
    play_list = list(tracks_by_filename.values())
    if args.where:
        for track in play_list[:]:
            album = track.album
            artist = track.artist
            title = track.title
            track_number = track.track_number
            where_result = eval(args.where)
            if not where_result:
                play_list.remove(track)
    #sort by file name by default
    play_list.sort(key=lambda track: str(track.file_object))
    order_string = ' '.join(args.order)
    comma_separated_orders = order_string.split(',')
    for order in reversed(comma_separated_orders):
        trimmed = order.strip()
        temp_arr = order.split()
        aspect = temp_arr[0]
        if aspect:
            pattern = 'asc'
            if len(temp_arr) > 1:
                pattern = temp_arr[1]
            backwards = False
            if pattern == 'desc':
                backwards = True
            def sort_value_function(track):
                aspect_value = getattr(track, aspect)
                if pattern =='random':
                    random.seed(str(aspect_value)+str(salt))
                    return random.randint(0, 999999999)
                else:
                    return aspect_value
            play_list.sort(reverse = backwards, key = sort_value_function)

    i = 0
    current_first_prop = None
    group_end = 0
    group_by_aspect = args.order[0]
    if(args.group_by):
        group_by_aspect = args.group_by
    while (args.all or group_end == 0) and i <= len(play_list):
        if i < len(play_list):
            track = play_list[i]
            prop = getattr(track, group_by_aspect)
        else:
            prop = ''
        if current_first_prop != prop:
            if i > 0:
                group_end = i
                print('\nPlaying {0}\n{1}\n'.format(group_by_aspect, current_first_prop))

                vlc_process = None
                params = []
                library_changed = False
                for track in play_list[group_start:group_end]:
                    if os.path.isfile(str(track.file_object)):
                        params.append(str(track.file_object))
                        if args.test:
                            print ('{0} - {1} - {2} - {3}'.format(track.artist, track.album, str(track.track_number), track.title))
                        else:
                            track.number_of_plays += 1
                            library_changed = True
                    else:
                        #no file to play, should remove track object from master list
                        print('no file found, removing from library {0}'.format(str(track.file_object)))
                        del tracks_by_filename[str(track.file_object)]
                        library_changed = True
                if len(params) > 0:
                    if platform.system() == 'Darwin':
                        params.insert(0, 'VLC')
                    else:
                        params.insert(0, 'vlc')
                    params.insert(1, '--play-and-exit')
                    if not args.test:
                        try:
                            vlc_process = subprocess.Popen(params, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except OSError:
                            print('unable to start VLC process. Make sure VLC is installed and added to PATH')
                if library_changed:
                    library_file = open(library_filename, 'wb')
                    pickle.dump(tracks_by_filename, library_file)
                    library_file.close()

                if args.all and i+1 < len(play_list) and vlc_process is not None:
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
                library_changed = True

    if library_changed:
        library_file = open(library_filename, 'wb')
        pickle.dump(tracks_by_filename, library_file)
        library_file.close()

elif args.command == 'audit':
    for filename, track in tracks_by_filename.items():
        if track.muta_file is None:
            track.muta_file = mutagen.File(track.file_object.absolute())
        for field in args.field:
            if field == 'track':
                if track.track_number is None or track.track_number == 0:
                    #could not find track number, try to figure it out
                    regex = re.search('^\d+', os.path.basename(str(track.file_object)))
                    if regex is not None:
                        maybe_track_number = int(regex.group())
                        print(f'no track number for file {filename}')
            elif field == 'album':
                if track.album is None or track.album == '':
                    print(f'no album name for file {filename}')
            elif field == 'artist':
                if track.artist is None or track.artist == '':
                    print(f'no artist for file {filename}')
            elif field == 'title':
                if track.title is None or track.title == '':
                    print(f'no title for file {filename}')
            elif field == 'type':
                if track.muta_file is not None and (isinstance(track.muta_file, mutagen.flac.FLAC) or isinstance(track.muta_file, mutagen.id3.ID3FileType) or isinstance(track.muta_file, mutagen.asf.ASF)):
                    #suppoted file
                    pass
                else:
                    print(f'type {track.muta_file.__class__.__name__} not yet supported for file {filename}')
