import json
import os
import sys
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
    config['m3u8'] = os.getenv("UP_m3u8", False)  # True/False
    config['ipfs_api'] = os.getenv("UP_ipfs_api")


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
    config["en_file"] = os.path.join(config['output_dir'], os.path.basename(config['input_file']))
    if os.path.isfile(config["en_file"]):
        os.remove(config["en_file"])
    stream = ffmpeg.input(infile)
    stream = ffmpeg.output(stream, config["en_file"], vcodec='libx264', acodec='aac',
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
    # TODO m3u8 切片
    pass


def up_ipfs(Filestore=False):
    api = ipfshttpclient.connect(config['ipfs_api'], timeout=3600)
    if config['mode'] == 'file':
        infile = config['en_file'] if config['encode'] else config['input_file']
        file_stats = os.stat(infile)
        fsize = file_stats.st_size
        if fsize > 1024 * 1024 * 5:
            h = api.add(infile, chunker='size-1048576', nocopy=Filestore)
        else:
            h = api.add(infile, nocopy=Filestore)
        return h['Hash']
    elif config['mode'] == 'm3u8':
        # TODO 将m3u8 文件上传到ipfs
        pass


if __name__ == '__main__':
    read_config()
    check()
    if config['encode']:
        encode()
    else:
        check_encode()
    if config['mode']:
        out_m3u8()

    if config['up_mode'] == 'ipfs':
        f_hash = up_ipfs()
    elif config['up_mode'] == 'ipfsFile':
        f_hash = up_ipfs(Filestore=True)

    print(f_hash)
    print("IPFS upload tool.")
