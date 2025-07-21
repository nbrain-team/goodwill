# Use the official Playwright image to get all browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script and the rest of the application code
COPY entrypoint.sh .
COPY ./app ./app

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Expose the port the app runs on
EXPOSE 10000

# Run the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"] 