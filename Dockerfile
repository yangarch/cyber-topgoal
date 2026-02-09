FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set locale to avoid encoding issues
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

COPY . .

# Create directory for data if it doesn't exist (though volume mount will handle it)
RUN mkdir -p /data /music

EXPOSE 8004

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
