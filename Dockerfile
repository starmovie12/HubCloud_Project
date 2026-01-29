# Base Image
FROM python:3.9

# 1. Zaroori tools install karo
RUN apt-get update && apt-get install -y wget unzip

# 2. Google Chrome Install karo (Direct Method - Bina Key ke)
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
RUN rm google-chrome-stable_current_amd64.deb

# 3. Setup Work Directory
WORKDIR /app
COPY . /app

# 4. Requirements Install karo
RUN pip install --no-cache-dir -r requirements.txt

# 5. App Start karo
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:10000", "--timeout", "120"]
