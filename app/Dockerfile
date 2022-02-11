# download the python image
FROM python:3.8

# set a directory for the app
WORKDIR /app

# install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

# run the command
ENTRYPOINT [ "python" ]
CMD [ "app.py" ]


#CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]