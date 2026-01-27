# dockerfile
# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Kopiraj Python pakete iz builder stage
COPY --from=builder /root/.local /root/.local

# Osiguraj da se pip paketi mogu koristiti
ENV PATH=/root/.local/bin:$PATH

# Kopiraj aplikaciju
COPY . .

# Pokreni aplikaciju sa gunicorn za production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app.main:app"]