# Dockerfile
FROM python:3.11-slim

# 1) set working directory
WORKDIR /app

# 2) install deps first (leverages Docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) copy your project code
COPY . .

# 4) default command
CMD ["python3", "-u", "main.py"]