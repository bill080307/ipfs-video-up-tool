import json
import os
import re
import sys
from urllib import parse

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import ffmpeg
import ipfshttpclient

config: dict = {}


def read_config():
    global config
    config['input_file'] = sys.argv[1]
    if len(sys.argv) >= 3:
        config['output_dir'] = sys.argv[2]
    else:
        config['output_dir'] = "/tmp"

    config['mode'] = os.getenv("UP_mode", "file")  # file/m3u8
    config['up_mode'] = os.getenv("UP_up_mode", "ipfs")  # ipfs/ipfsFile/web3/fileCoin
    config['encode'] = os.getenv("UP_encode", False)  # True/False
    config['ipfs_api'] = os.getenv("UP_ipfs_api")
    config['web3_token'] = os.getenv("UP_web3_token")


def getvideofileinfo(filepath):
    path = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    os.chdir(path)
    output = os.popen(
        u'ffprobe -v quiet -print_format json -show_format -show_streams %s' % filename)
    return json.loads(output.read())


def check():
    if not os.path.isfile(config['input_file']):
        print("input is not a file")
        exit(1)
    try:
        config['videoinfo'] = getvideofileinfo(config['input_file'])
    except:
        print("input file is not a video")
        exit(1)
    if config['up_mode'] in ['ipfs', 'ipfsFile']:
        if not config['ipfs_api']:
            print("ipfs mode api is must")
            exit(1)


def encode():
    infile = config['input_file']
    basename = os.path.splitext(os.path.basename(config['input_file']))[0] + ".mp4"
    config["en_file"] = os.path.join(config['output_dir'], basename)
    if os.path.isfile(config["en_file"]):
        os.remove(config["en_file"])
    info = config['videoinfo']

    vcodec = "copy"
    acodec = "copy"
    for stream in info['streams']:
        if stream['codec_type'] == "audio":
            if not stream['codec_name'] == 'aac':
                acodec = "aac"
        elif stream['codec_type'] == "video":
            if not stream['codec_name'] == 'h264':
                vcodec = "libx264"
    stream = ffmpeg.input(infile)
    stream = ffmpeg.output(stream, config["en_file"], vcodec=vcodec, acodec=acodec,
                           f='mp4', )
    stream.run()
    config['videoinfo'] = getvideofileinfo(config['en_file'])


def check_encode():
    info = config['videoinfo']
    if not info['format']['format_name'] == 'mov,mp4,m4a,3gp,3g2,mj2':
        print("file is not mp4 format")
        exit(1)
    for stream in info['streams']:
        if stream['codec_type'] == "audio":
            if not stream['codec_name'] == 'aac':
                print("file is not aac audio format")
                exit(1)
        elif stream['codec_type'] == "video":
            if not stream['codec_name'] == 'h264':
                print("file is not h264 video format")
                exit(1)


def out_m3u8():
    HLS_TIME = 30
    infile = config['en_file'] if config['encode'] else config['input_file']
    basename = os.path.splitext(os.path.basename(infile))[0]
    tempDir = os.path.join(config['output_dir'], basename)
    os.mkdir(tempDir)
    os.chdir(tempDir)
    cmd = u"ffmpeg -i %s -vcodec copy -acodec copy -f segment -segment_time %s -hls_playlist_type vod -segment_list %s.m3u8 %s_%%03d.ts" \
          % (infile, HLS_TIME, 'index', 'video')
    print(cmd)
    output = os.popen(cmd)
    print(output.read())
    config['m3u8_dir'] = tempDir


def up_ipfs(Filestore=False):
    api = ipfshttpclient.connect(config['ipfs_api'], timeout=3600)
    ipfs_conf = api.config.get()
    if Filestore and not ipfs_conf['Experimental']['FilestoreEnabled']:
        print('ipfs node Filestore is disable')
        exit(1)
    if config['mode'] == 'file':
        infile = config['en_file'] if config['encode'] else config['input_file']
        file_stats = os.stat(infile)
        fsize = file_stats.st_size
        if fsize > 1024 * 1024 * 5:
            h = api.add(infile, chunker='size-1048576', nocopy=Filestore, cid_version=1)
        else:
            h = api.add(infile, nocopy=Filestore, cid_version=1)
        return h['Hash']
    elif config['mode'] == 'm3u8':
        m3u8_file = os.path.join(config['m3u8_dir'], 'index.m3u8')
        with open(m3u8_file, "r") as f:
            m3u8 = f.read()
        m3u8_new = m3u8
        m3u8_ts = re.findall(r'#EXTINF:.*\n(video_.*\.ts)', m3u8)
        for ts in m3u8_ts:
            infile = os.path.join(config['m3u8_dir'], ts)
            file_stats = os.stat(infile)
            fsize = file_stats.st_size
            if fsize > 1024 * 1024 * 5:
                h = api.add(infile, chunker='size-1048576', nocopy=Filestore, cid_version=1)
            else:
                h = api.add(infile, nocopy=Filestore, cid_version=1)
            m3u8_new = m3u8_new.replace(ts, "/ipfs/" + h['Hash'])
        with open(os.path.join(config['m3u8_dir'], 'index_ipfs.m3u8'), "w") as f:
            f.write(m3u8_new)
        h = api.add(os.path.join(config['m3u8_dir'], 'index_ipfs.m3u8'), nocopy=Filestore, cid_version=1)
        return h['Hash']


def up_web3():
    def up(file):
        url = 'https://api.web3.storage/upload'
        name = os.path.basename(file)
        data = MultipartEncoder(fields={'file': (name, open(file, 'rb'), 'application/octet-stream')})
        headers = {
            "accept": "application/json",
            'X-Name': parse.quote(name),
            "Content-Type": data.content_type,
            "Authorization": "Bearer " + config['web3_token']
        }
        response = requests.request("POST", url, data=data, headers=headers)
        return json.loads(response.text)

    m3u8_file = os.path.join(config['m3u8_dir'], 'index.m3u8')
    with open(m3u8_file, "r") as f:
        m3u8 = f.read()
    m3u8_new = m3u8
    m3u8_ts = re.findall(r'#EXTINF:.*\n(video_.*\.ts)', m3u8)
    for ts in m3u8_ts:
        infile = os.path.join(config['m3u8_dir'], ts)
        h = up(infile)
        m3u8_new = m3u8_new.replace(ts, "/ipfs/" + h['cid'])
    with open(os.path.join(config['m3u8_dir'], 'index_ipfs.m3u8'), "w") as f:
        f.write(m3u8_new)
    h = up(os.path.join(config['m3u8_dir'], 'index_ipfs.m3u8'))
    return h['cid']


if __name__ == '__main__':
    read_config()
    check()
    if config['encode']:
        encode()
    else:
        check_encode()
    if config['mode'] == 'm3u8':
        out_m3u8()

    if config['up_mode'] == 'ipfs':
        f_hash = up_ipfs()
    elif config['up_mode'] == 'ipfsFile':
        f_hash = up_ipfs(Filestore=True)
    elif config['up_mode'] == 'web3':
        f_hash = up_web3()

    print(f_hash)
    print("IPFS upload tool.")
