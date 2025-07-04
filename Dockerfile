FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app


# Copy application files
COPY bot.py .
COPY requirements.txt .

RUN apt update -y && apt install -y python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages

# Create botuser and set ownership after copying files
RUN addgroup --system botuser && adduser --system --ingroup botuser botuser \
    && chown -R botuser:botuser /app

USER botuser

ENTRYPOINT ["python3", "bot.py"]