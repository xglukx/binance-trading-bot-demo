FROM python:3.9-slim

WORKDIR /app

# Install build dependencies for psutil and timezone data
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure timezone
ENV TZ=Asia/Singapore
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install compatible Flask version first with specific compatible dependencies
RUN pip install markupsafe==1.1.1 Jinja2==2.11.3 itsdangerous==1.1.0 werkzeug==1.0.1 flask==1.1.2

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip freeze > /installed_deps.txt

# Print Python environment info for debugging
RUN python -m pip list && python --version && echo "Python environment ready" && cat /installed_deps.txt

# Copy application files
COPY trading_bot_fly.py .
COPY .env .env

# Create data directory for persistence with proper permissions
RUN mkdir -p /data && chmod 777 /data && chown nobody:nogroup /data && ls -la /data

# Make the script executable
RUN chmod +x trading_bot_fly.py

# Environment variables to reduce memory usage
ENV PYTHONUNBUFFERED=1
ENV PYTHONMALLOC=malloc
ENV OPENBLAS_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1
ENV OMP_NUM_THREADS=1
ENV HISTORY_LIMIT=100
ENV PYTHONGC=aggressive
ENV PYTHONUTF8=1

# Setting pandas to use less memory
ENV PANDAS_CHUNKSIZE=1000

# Expose the port
EXPOSE 8080

# Run the application with Gunicorn with memory optimization
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "2", "--max-requests", "50", "--max-requests-jitter", "5", "--log-level", "debug", "--preload", "--timeout", "60", "trading_bot_fly:app"] 