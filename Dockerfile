FROM python:latest
WORKDIR /App
COPY . ./
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "python3" ]
CMD [ "ssafumadmin.py" ]