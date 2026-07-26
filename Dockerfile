# Legacy HF Streamlit image (Space uses sdk: streamlit from README).
# For the production FastAPI API host, use Dockerfile.api + render.yaml instead.
#
# Use an official Python runtime
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your entire project (including the frontend folder) into the container
COPY . .

# Expose the port Hugging Face expects
EXPOSE 8000

# Run the app from inside the frontend folder
# NOTE: Adjust this bottom line based on what you are using (FastAPI, Streamlit, etc.)
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8000", "--server.address=0.0.0.0"]
