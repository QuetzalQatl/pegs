FROM baskoning/gamebase:latest

RUN mkdir files
COPY . /files/
WORKDIR /files

ARG LANIP="192.168.99.100"
ENV LANIP="${LANIP}"

ARG PORT=5000
ENV PORT="${PORT}"

EXPOSE ${PORT}

CMD python startserver.py
