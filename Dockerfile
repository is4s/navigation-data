FROM ubuntu:24.04

RUN apt update && apt install python3-pip -y

RUN pip install twine==6.1.0 --break-system-packages

WORKDIR /work
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["/bin/bash"]
