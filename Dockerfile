FROM postgres:14-bullseye

RUN apt update
RUN apt install -y postgresql-14-postgis-3 libcurl4-openssl-dev git build-essential postgresql-server-dev-14 curl \
  python postgresql-plpython3-14 python3-pip

# Install pgsql-http extension
RUN cd /usr; \
  git clone https://github.com/pramsey/pgsql-http.git; \
  cd /usr/pgsql-http; \
  make && make install

RUN pip install metar
