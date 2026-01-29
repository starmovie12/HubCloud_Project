FROM python:3.9

# 1. Install Chrome & Dependencies
RUN apt-get update && apt-get install -y wget unzip
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
RUN rm google-chrome-stable_current_amd64.deb

# 2. Setup App
WORKDIR /app
COPY . /app

# 3. Install Python Libs
RUN pip install --no-cache-dir -r requirements.txt

# 4. Run App
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:10000", "--timeout", "120"]
