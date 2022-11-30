FROM python:3.5

ENV EDITOR=vi \
    PYTHONUNBUFFERED=1 \
    TZ=America/New_York \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -yq --no-install-recommends \
        locales \
        vim \
        cron \
        htop \
        less \
        tree \
        audiotools \
        sox \
        graphviz \
        graphviz-dev \
        python-pil \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

COPY pip_packages /tmp/pip_packages
COPY requirements.txt /tmp/pip_tmp/
COPY requirements_dev.txt /tmp/pip_tmp/
RUN pip --no-cache-dir install --upgrade pip  \
    && pip --no-cache-dir install -r /tmp/pip_tmp/requirements.txt \
    && pip install /tmp/pip_packages/* \
    && rm -rf /tmp/pip_tmp \
    && rm -rf /tmp/pip_packages

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog

# Link missing auditools modules
RUN ln -s /usr/lib/python3/dist-packages/audiotools/pcm.cpython-36m-x86_64-linux-gnu.so /usr/lib/python3/dist-packages/audiotools/pcm.so && \
    ln -s /usr/lib/python3/dist-packages/audiotools/pcmconverter.cpython-36m-x86_64-linux-gnu.so /usr/lib/python3/dist-packages/audiotools/pcmconverter.so && \
    ln -s /usr/lib/python3/dist-packages/audiotools/bitstream.cpython-36m-x86_64-linux-gnu.so /usr/lib/python3/dist-packages/audiotools/bitstream.so && \
    ln -s /usr/lib/python3/dist-packages/audiotools/encoders.cpython-36m-x86_64-linux-gnu.so /usr/lib/python3/dist-packages/audiotools/encoders.so && \
    ln -s /usr/lib/python3/dist-packages/audiotools/_ogg.cpython-36m-x86_64-linux-gnu.so /usr/lib/python3/dist-packages/audiotools/_ogg.so && \
    ln -s /usr/lib/python3/dist-packages/audiotools/_accuraterip.cpython-36m-x86_64-linux-gnu.so /usr/lib/python3/dist-packages/audiotools/_accuraterip.so && \
    ln -s /usr/lib/python3/dist-packages/audiotools/cdio.cpython-36m-x86_64-linux-gnu.so /usr/lib/python3/dist-packages/audiotools/cdio.so && \
    ln -s /usr/lib/python3/dist-packages/audiotools/decoders.cpython-36m-x86_64-linux-gnu.so /usr/lib/python3/dist-packages/audiotools/decoders.so && \
    ln -s /usr/lib/python3/dist-packages/audiotools/output.cpython-36m-x86_64-linux-gnu.so /usr/lib/python3/dist-packages/audiotools/output.so && \
    ln -s /usr/lib/python3/dist-packages/audiotools/replaygain.cpython-36m-x86_64-linux-gnu.so /usr/lib/python3/dist-packages/audiotools/replaygain.so && \
    ln -s /usr/lib/python3/dist-packages/audiotools /usr/local/lib/python3.5/site-packages/audiotools

EXPOSE 8000
