# ipfs-video-up-tool
ipfs协议的视频辅助上传工具

# 功能
1. - [x] 支持在线播放的编码检测
2. - [x] 支持转码，转成支持在线播放的编码标准
3. - [x] 支持切片，
4. - [x] 支持上传到自行搭建的ipfs节点,单文件形式
5. - [x] 支持上传到自行搭建的ipfs节点,m3u8形式
6. - [x] 支持上传到ipfs节点的Filestore方式,单文件形式
7. - [x] 支持上传到ipfs节点的Filestore方式,m3u8形式
8. - [x] 支持上传到web3.storage,支持m3u8形式

# 流程图
![FlowChart](img/FlowChart.png)

# 使用说明
## 安装
### ubuntu中直接安装
~~~bash
apt install -y python3 python3-pip ffmpeg
pip3 install -r requirements.txt
~~~
### 使用docker
~~~bash
docker build -t ipfs-video-up-tool:v0.0.1 .
~~~

## 选项
###  ubuntu中直接运行
本脚本通过环境变量传递选项
~~~bash
export UP_mode=file                        # 上传的方式，支持file单文件模式;m3u8切片模式
export UP_up_mode=ipfs                     # 存储方式，支持ipfs普通模式;ipfsFile(ipfs启用Filestore的方式);web3使用协议实验室的web3.storage;fileCoin直接使用filecoin主网络
export UP_encode=False                     # 是否启用转码，为了更好的适配HTML5，开启转码将会转成h264/aac格式
export UP_ipfs_api=/ip4/127.0.0.1/tcp/5001 # 传递ipfs的api地址，采用多地址格式(Multiaddr)
export UP_web3_token=eyJhbG.....           # 使用web3作为存储时，web3帐号的token

python3 Update.py Example.mkv          #脚本第一个参数为输入的文件。
python3 Update.py Example.mkv /output  #脚本第二个参数为输出文件夹。
~~~
特别注意：使用Filestore时，1. 运行脚本的文件系统和ipfs node所在的文件系统要同时在相同路径上挂载被上传的文件；2. ipfs repo和被上传的文件根目录需要使用同一个；3. 需要转换文件时，如UP_encode=True或者UP_mode=m3u8时上传的是output文件夹内的文件，否则为输入文件本身；
### 使用docker运行
~~~bash
docker run \
    -e UP_mode=file \
    -e UP_up_mode=ipfs \
    -e UP_encode=False \
    -e UP_ipfs_api=/ip4/127.0.0.1/tcp/5001 \
    -e UP_web3_token=eyJhbG..... \
    -v /input_dir:/data \
    -itd /data/Example.mkv
~~~

