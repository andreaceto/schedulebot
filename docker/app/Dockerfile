# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system build dependencies required for llama-cpp-python
# build-essential includes compilers like gcc and g++
# cmake is also required by the build process
RUN apt-get update && apt-get install -y build-essential cmake

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir: Disables the cache to keep the image size smaller
# --trusted-host pypi.python.org: Can help avoid SSL issues in some networks
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt
# Download the spaCy model using its own command line interface
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application's source code from your host to your image filesystem.
COPY ./src /app/src
COPY ./models /app/models
COPY .env /app/.env

# Command to run the application when the container launches
# This will be the main entry point for your Gradio app in the next milestone.
# For now, we can use the command-line chat.
CMD ["python", "-m", "run_app.py"]
