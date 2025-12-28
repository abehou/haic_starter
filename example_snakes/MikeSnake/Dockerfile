FROM python:3.10.6-slim

# Install app
COPY . /usr/app
WORKDIR /usr/app

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Set default port but allow override via environment variable
ENV PORT=7123

# Expose the port
EXPOSE $PORT

# Run Battlesnake
CMD [ "python", "main.py" ]
