FROM mdiazipass/alpine3.8-python3.7-bash

COPY . /app/

WORKDIR /app/

RUN pip install flask flask_restful flask_restplus

ENV APP_HOME=http://seat.stdio.ml

ENTRYPOINT [ "python","-u","./test.py" ]