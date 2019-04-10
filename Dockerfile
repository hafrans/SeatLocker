FROM mdiazipass/alpine3.8-python3.7-bash

COPY . /app/

WORKDIR /app/

RUN pip install flask flask_restful flask_restplus flask_compress redis

ENV APP_HOST=http://seathelper.ml

ENV APP_ORIGIN=ujn.seathelper.ml;lcu.seathelper.ml;ujn.seathelper.ml:8081;lcu.seathelper.ml:8081

EXPOSE 5000

VOLUME /app/data/db/

ENTRYPOINT [ "python","-u","init.py"]

CMD ["server","standalone"]