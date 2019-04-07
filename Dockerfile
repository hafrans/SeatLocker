FROM mdiazipass/alpine3.8-python3.7-bash

COPY ./data /app/
COPY ./seat /app/
COPY ./server /app/
COPY ./test.py /app/

WORKDIR /app/

RUN pip install flask flask_restful flask_restplus flask_compress

ENV APP_HOME=http://seat.stdio.ml

ENTRYPOINT [ "python","-u","./test.py" ]