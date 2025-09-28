import asyncio
import copy
import glob
import json
import math
import os
import pygit2
import shutil

import xml.etree.ElementTree as ET

from dotenv import load_dotenv
from ipytv import playlist


async def probe(stream, timeout, duration):

    # try to cut down on false positives by using ffmpeg to
    # transcode a finite duration rather than ffprobe.
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-re",
        "-hide_banner",
        "-rw_timeout",
        str(math.ceil(timeout * 1.e6)),
        "-i",
        stream.url,
        "-f",
        "null",
        "-t",
        str(duration),
        "-",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )

    return await asyncio.wait_for(proc.wait(), timeout = (2.0 * timeout))

async def generate():

    #options

    livetv_dir: str = os.getenv("LIVETV_DIR", "livetv");

    playlist_upstream: str = os.getenv("PLAYLIST_UPSTREAM", "https://iptv-org.github.io/iptv/index.m3u")
    playlist_m3u: str = os.getenv("PLAYLIST_M3U", os.path.join(livetv_dir, "playlist.m3u"))

    epg_upstream: str = os.getenv("EPG_UPSTREAM", "https://github.com/iptv-org/epg.git")
    epg_local: str = os.getenv("EPG_LOCAL", os.path.join(livetv_dir, "epg.git"))
    epg_xml: str = os.getenv("EPG_XML", os.path.join(livetv_dir, "channels.xml"))

    probes_batch: int = int(os.getenv("PROBES_BATCH", "25")) # concurrent probe subprocesses
    probes_timeout: float = float(os.getenv("PROBES_TIMEOUT", "15.0")) # timeout in seconds
    probes_duration: float = float(os.getenv("PROBES_DURATION", "5.0")) # output duration in seconds

    shutil.rmtree(path = epg_local, ignore_errors=True)

    pygit2.clone_repository(url = epg_upstream, path = epg_local, depth = 1)

    channels_by_id: dict = {}

    for channels in glob.iglob("sites/**/*channels.xml", root_dir = epg_local, recursive = True):
        fqn: str = os.path.join(epg_local, channels)
        data = ET.parse(fqn).getroot()
        for channel in data.iter("channel"):
            if ("en" == channel.attrib["lang"]):
                xmltv_id = channel.attrib["xmltv_id"]
                if xmltv_id:
                    channels_by_id[xmltv_id] = channel
    print(f"channels: {len(channels_by_id)}")

    pl_all = playlist.loadu(playlist_upstream)

    tvgs_regex = r"^[\S\s]+$"
    tvgs = pl_all.search(tvgs_regex, where="attributes.tvg-id", case_sensitive=False)
    pl_tvgs = playlist.M3UPlaylist()
    pl_tvgs.append_channels(tvgs)

    geos_regex = r"^((?!blocked).)*$"
    geos = pl_tvgs.search(geos_regex, where="name", case_sensitive=False)

    print(f"filtered streams: {len(geos)}")

    guided_streams = [stream for stream in geos if stream.attributes["tvg-id"] in channels_by_id.keys()]

    print(f"guided streams: {len(guided_streams)}")

    live_streams = []
    outstanding = copy.deepcopy(guided_streams)

    while outstanding:

        streams = outstanding[-probes_batch:]
        del outstanding[-probes_batch:]
        procs = [probe(stream, probes_timeout, probes_duration) for stream in streams ]
        rtns = await asyncio.gather(*procs, return_exceptions=True)
        live_streams += [stream for stream, rtn in zip(streams, rtns) if 0 == rtn]
        print(f"outstanding: {len(outstanding)}\tlive: {len(live_streams)}\trtns: {rtns}")

        await asyncio.sleep(0) # give others a chance to run

    fixed_pl = playlist.M3UPlaylist()
    fixed_pl.append_channels(live_streams)

    with open(playlist_m3u, 'w', encoding='utf-8') as playlist_file:
            content = fixed_pl.to_m3u_plus_playlist()
            playlist_file.write(content)

    live_ids = [stream.attributes["tvg-id"] for stream in live_streams]

    live_channels = [channel for tvg_id, channel in channels_by_id.items() if tvg_id in live_ids]

    tree = ET.Element("channels")
    for channel in live_channels:
        tree.append(channel)

    ET.indent(tree)
    ET.ElementTree(tree).write(epg_xml, encoding="UTF-8", xml_declaration=True)


if __name__ == '__main__':
    load_dotenv()
    asyncio.run(generate())
