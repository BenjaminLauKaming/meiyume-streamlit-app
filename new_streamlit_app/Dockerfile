FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the ports for Streamlit and the webhook server
EXPOSE 8501
EXPOSE 5001

# The command to run the Streamlit app
CMD ["streamlit", "run", "main.py"]