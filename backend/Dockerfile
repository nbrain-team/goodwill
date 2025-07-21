# Use the official Playwright image to get all browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code
COPY ./app ./app

# The command to run the application will be specified in render.yaml
# But we can add a default command here for local testing
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"] 