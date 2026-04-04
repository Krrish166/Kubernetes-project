FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080

# Default Rest API URL
ENV API_URL=http://localhost:8081

CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]