FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY app/ app/

ENV RELAY_API_KEY=""
ENV RELAY_APNS_KEY_ID=""
ENV RELAY_APNS_TEAM_ID=""
ENV RELAY_APNS_BUNDLE_ID="dev.flux-notifier.app"
ENV RELAY_APNS_PRIVATE_KEY=""
ENV RELAY_APNS_PRODUCTION="false"
ENV RELAY_FCM_SERVER_KEY=""

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
