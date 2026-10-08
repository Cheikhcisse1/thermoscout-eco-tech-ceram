FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m app && chown -R app /app
USER app
# En ligne : mot de passe obligatoire, sauf en démo publique (PUBLIC_MODE=1, IA gratuite Gemini)
ENV REQUIRE_AUTH=1 DEFAULT_PROVIDER=anthropic
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
