FROM continuumio/miniconda3

# Set the working directory in the container to /app
WORKDIR /app

# Install the required packages
COPY environment.yaml /app
RUN conda env create -f /app/environment.yaml
ARG hftoken
# Copy the app itself
RUN mkdir -p /app/uploads
COPY app.py config.py ./

# Make port 5000 available to the world outside this container
EXPOSE 5001

# Define environment variable for Flask to run on 0.0.0.0
ENV FLASK_RUN_HOST=0.0.0.0

# Run the command to start your app
CMD ["/opt/conda/envs/mistral/bin/gunicorn", "-b", "0.0.0.0:5001", "--workers", "1", "--timeout", "500", "app:app"]
