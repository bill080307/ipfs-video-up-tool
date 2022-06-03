FROM ubuntu:22.04
COPY sources.list /etc/apt/
RUN apt update \
 && apt install -y python3 python3-pip ffmpeg
COPY Upload.py /
COPY requirements.txt /
RUN pip3 install -r requirements.txt
RUN sed -i 's/VERSION_MAXIMUM   = "0.8.0"/VERSION_MAXIMUM   = "0.13.0"/' /usr/local/lib/python3.10/dist-packages/ipfshttpclient/client/__init__.py
ENTRYPOINT ["python3", "/Upload.py"]