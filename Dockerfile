FROM baskoning/gamebase:latest

COPY Files /

ARG LANIP="192.168.99.100"
ENV LANIP="${LANIP}"
ARG PORT=5000
ENV PORT="${PORT}"

EXPOSE ${PORT}

CMD python startflask.py
