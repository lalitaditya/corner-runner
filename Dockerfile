FROM python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 AS runtime
FROM runtime AS build
RUN apt-get update && apt-get install -y --no-install-recommends g++ && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir Cython==3.2.4 setuptools==80.9.0
WORKDIR /build
COPY build_world.py spatial.pyx ./
RUN python build_world.py build_ext --inplace

FROM runtime
WORKDIR /bot
COPY --from=build /build/spatial*.so ./
COPY bot.py decisions.py protocol.py world.py gorandom.py semantics.py campus.nav hidemap.gz ./
COPY LICENSE ./
COPY licenses/ licenses/
ENTRYPOINT ["python3", "-B", "-u", "/bot/bot.py"]
