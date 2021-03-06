FROM ubuntu:14.04
MAINTAINER Gunnar H. Heinesen "gunnar@magenta.dk"
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential sqlite3
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["application.py"]
