# using small new python
FROM python:3.11-slim

# stop pip from writing .pyc and enable unbuffered stdout, sure
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Workdir inside the image, sure,
WORKDIR /app

# Install deps first (use layer caching) - ya that's fait
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run your app (prints live logs)
CMD ["python3", "-u", "main.py"]
