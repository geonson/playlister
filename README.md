# playlister
Command line utility for quickly generating playlists for VLC

Requires python3, mutagen package, and VLC added to PATH

## Examples:

Import media files in current directory to library data (so you can generate playlists with them):  
`python playlister.pyx import .`

Play all library files, sorting by album randomly, open in VLC one album at a time
`python playlister.pyx play --all album random --group-by album`

For all command use instructions:
`python playlister.pyx --help`
