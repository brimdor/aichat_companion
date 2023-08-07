FROM brimdor/brobot:latest

RUN mkdir /app
RUN chmod -R 755 /app
WORKDIR /app
RUN mkdir templates

RUN python3 -m pip install openai python-dotenv discord

ADD * .

USER root

RUN chmod -R 750 *                      

ENTRYPOINT ["bash","./entrypoint.sh"]