FROM python:3.10-bullseye

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    LIBGL_ALWAYS_SOFTWARE=1 \
    QT_X11_NO_MITSHM=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    XDG_RUNTIME_DIR=/tmp/runtime-spycer

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    fluxbox \
    libdbus-1-3 \
    libegl1 \
    libfontconfig1 \
    libgl1 \
    libglib2.0-0 \
    libglu1-mesa \
    libgomp1 \
    libnss3 \
    libsm6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-render0 \
    libxcb-shape0 \
    libxcb-shm0 \
    libxcb-sync1 \
    libxcb-util1 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcomposite1 \
    libxcursor1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxkbcommon-x11-0 \
    libxkbcommon0 \
    libxrender1 \
    libxtst6 \
    novnc \
    procps \
    websockify \
    x11vnc \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

COPY linux-req.txt requirements.txt ./

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install -r linux-req.txt

COPY . .
COPY docker/start-spycer.sh /usr/local/bin/start-spycer

RUN chmod +x /usr/local/bin/start-spycer \
    && mkdir -p "$XDG_RUNTIME_DIR"

EXPOSE 5900 6080

CMD ["/usr/local/bin/start-spycer"]
