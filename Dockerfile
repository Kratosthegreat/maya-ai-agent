FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    pkg-config \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libx11-dev \
    libxrandr-dev \
    libxcursor-dev \
    libxinerama-dev \
    libxi-dev \
    libxext-dev \
    && rm -rf /var/lib/apt/lists/*

# הגדרה מפורשת של PKG_CONFIG_PATH כדי ש-go-gl/gl ימצא gl.pc
ENV PKG_CONFIG_PATH="/usr/lib/x86_64-linux-gnu/pkgconfig"

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN groupadd -r maya && useradd -r -g maya maya
RUN chown -R maya:maya /app
USER maya

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

CMD ["python", "main.py"]