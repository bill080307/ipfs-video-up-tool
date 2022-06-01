FROM ubuntu:22.04
RUN apt update \
 && apt install -y python3
COPY Upload.py /
CMD ["python3", "/Upload.py"]