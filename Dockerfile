FROM lucascosta/serverless-python3.6:lastest

COPY . /app/

WORKDIR /app/

RUN pip install flask flask_restful

ENTRYPOINT [ "python","-u","./test.py" ]