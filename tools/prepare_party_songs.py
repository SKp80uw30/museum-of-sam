"""
Extract nominated Spotify songs from characters/messages.txt into a small
JSON file the homepage's "Party" feature can fetch at runtime.

Run from the repo root:

    python3 tools/prepare_party_songs.py

characters/ is gitignored (personal source photos live there) and is never
served by the site, so its "Spotify Song Link" fields have to be copied out
into web/ to be usable in the browser. Only the character name and Spotify
track link are extracted here — the file's other optional fields (Birthday
Message, Surprise Message) aren't used by anything yet, so this only reads
what today's feature needs. Re-run any time someone fills in a new Spotify
link in messages.txt; the output is fully regenerated each run, so a
removed link stops appearing too.
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = REPO_ROOT / "characters" / "messages.txt"
OUT_PATH = REPO_ROOT / "web" / "party-songs.json"

TRACK_ID_RE = re.compile(r"open\.spotify\.com/track/([A-Za-z0-9]+)")


def parse_blocks(text):
    blocks = re.split(r"^\s*---\s*$", text, flags=re.MULTILINE)
    for block in blocks:
        fields = {}
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
        if fields:
            yield fields


def main():
    if not SRC_PATH.is_file():
        print(f"Source file not found: {SRC_PATH}", file=sys.stderr)
        sys.exit(1)

    songs = []
    for fields in parse_blocks(SRC_PATH.read_text()):
        character = fields.get("Character")
        link = fields.get("Spotify Song Link")
        if not character or not link:
            continue
        match = TRACK_ID_RE.search(link)
        if not match:
            print(f"Skipping {character}: couldn't find a track id in {link!r}", file=sys.stderr)
            continue
        songs.append({"character": character, "url": link, "trackId": match.group(1)})

    OUT_PATH.write_text(json.dumps(songs, indent=2) + "\n")
    print(f"Wrote {len(songs)} nominated song(s) to {OUT_PATH}")
    for song in songs:
        print(f"  {song['character']}: {song['trackId']}")


if __name__ == "__main__":
    main()
