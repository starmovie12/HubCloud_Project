# Base Python Image
FROM python:3.9

# 1. Install Dependencies & Chrome (Direct Method - No apt-key needed)
RUN apt-get update && apt-get install -y wget unzip && \
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb && \
    apt-get clean

# 2. Setup Work Directory
WORKDIR /app
COPY . /app

# 3. Install Python Requirements
RUN pip install --no-cache-dir -r requirements.txt

# 4. Run App (Gunicorn binds to Render's default port 10000)
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:10000", "--timeout", "120"]
