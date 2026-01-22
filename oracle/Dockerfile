FROM wolframresearch/wolframengine:latest

USER root

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages flask wolframclient

COPY kernel_manager.py /oracle/kernel_manager.py
COPY server.py /oracle/server.py
COPY init.wl /oracle/init.wl

WORKDIR /oracle

EXPOSE 8765

CMD ["python3", "server.py"]
