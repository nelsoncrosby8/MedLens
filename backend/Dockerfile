# MedLens backend. Used both as the docker-compose dev image (source bind-mounted,
# UVICORN_RELOAD=1 for hot reload) and as the image deployed to Render (which assigns
# $PORT and does not set UVICORN_RELOAD). TensorFlow makes this image large (~1.5 GB).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# libgomp1: OpenMP runtime needed by scipy / scikit-learn wheels.
# curl: docker-entrypoint.sh uses it to fetch the model weights at startup on deploys
# where they aren't bind-mounted from the host.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
# Shell form so $PORT (set by the hosting platform) and the optional --reload flag
# (set locally via UVICORN_RELOAD) are expanded at container start, not build time.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} ${UVICORN_RELOAD:+--reload}"]
