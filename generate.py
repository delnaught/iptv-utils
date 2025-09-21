import glob
import json
import os
import pygit2
import shutil

import xml.etree.ElementTree as ET

from dotenv import load_dotenv
from ipytv import playlist

load_dotenv()

#options

livetv_dir: str = os.getenv("LIVETV_DIR", "livetv");

playlist_upstream: str = os.getenv("PLAYLIST_UPSTREAM", "https://iptv-org.github.io/iptv/index.m3u")
playlist_m3u: str = os.getenv("PLAYLIST_M3U", os.path.join(livetv_dir, "playlist.m3u"))

epg_upstream: str = os.getenv("EPG_UPSTREAM", "https://github.com/iptv-org/epg.git")
epg_local: str = os.getenv("EPG_LOCAL", os.path.join(livetv_dir, "epg.git"))
epg_xml: str = os.getenv("EPG_XML", os.path.join(livetv_dir, "channels.xml"))

shutil.rmtree(path = epg_local, ignore_errors=True)

pygit2.clone_repository(url = epg_upstream, path = epg_local, depth = 1)

xmltv_ids: set = set()

channels_by_id: dict = {}

for channels in glob.iglob("sites/**/*channels.xml", root_dir = epg_local, recursive = True):
    fqn: str = os.path.join(epg_local, channels)
    data = ET.parse(fqn).getroot()
    for channel in data.iter("channel"):
        if ("en" == channel.attrib["lang"]):
            xmltv_id = channel.attrib["xmltv_id"]
            if xmltv_id:
                xmltv_ids.add(xmltv_id)
                channels_by_id[xmltv_id] = channel

feeds_by_id: dict = {}
pl_all = playlist.loadu(playlist_upstream)

tvgs_regex = r"^[\S\s]+$"
tvgs = pl_all.search(tvgs_regex, where="attributes.tvg-id", case_sensitive=False)
pl_tvgs = playlist.M3UPlaylist()
pl_tvgs.append_channels(tvgs)

geos_regex = r"^((?!blocked).)*$"
geos = pl_tvgs.search(geos_regex, where="name", case_sensitive=False)

fixed_pl = playlist.M3UPlaylist()
for channel in geos:
    xmltv_id = channel.attributes["tvg-id"]
    if xmltv_id in xmltv_ids:
        feeds_by_id[xmltv_id] = channel
        fixed_pl.append_channel(channel)

with open(playlist_m3u, 'w', encoding='utf-8') as playlist_file:
        content = fixed_pl.to_m3u_plus_playlist()
        playlist_file.write(content)

xmltv_ids = set(feeds_by_id.keys())
channels_by_id = {  k:v for (k,v) in channels_by_id.items() if k in xmltv_ids }

print(f" feeds: {len(feeds_by_id)} and channels: {len(channels_by_id)}")

tree = ET.Element("channels")
for channel in channels_by_id.values():
    tree.append(channel)

ET.indent(tree)
ET.ElementTree(tree).write(epg_xml, encoding="UTF-8", xml_declaration=True)
