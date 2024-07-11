FROM python:3-alpine
WORKDIR /bot
COPY /bot.py /bot/bot.py
COPY /main.py /bot/main.py
COPY /mqtt_client.py /bot/mqtt_client.py
COPY /consts.py /bot/consts.py
COPY /__init__.py /bot/__init__.py
RUN python3 -m pip install python-telegram-bot
RUN python3 -m pip install paho-mqtt
CMD [ "python3", "main.py" ]
