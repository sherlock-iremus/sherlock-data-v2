FROM python:3.8
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN useradd -r app
USER app
ENV TERM=linux
ENV TERMINFO=/etc/terminfo
CMD ["python", "./rdfizers/indexations-caca-to-directus.py"]