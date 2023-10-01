FROM ubuntu:lunar-20230731

RUN mkdir -p /app/config
RUN chmod -R 755 /app
WORKDIR /app

ADD bot.py .
ADD requirements.txt .

RUN apt update -y && apt install python3-pip -y
# RUN python3 -m pip install openai python-dotenv discord
RUN pip install -r requirements.txt

USER root

RUN chmod -R 750 *                      

ENTRYPOINT ["python3","bot.py"]