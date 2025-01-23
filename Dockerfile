FROM python:3.12.7

# Create a working directory (optional but recommended)
WORKDIR /app

# Copy only requirements.txt first for better build caching
COPY requirements.txt /app/

# Now install those dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Then copy the rest of your code into the container
COPY . /app/

# Expose port if using a web server
EXPOSE 7860

CMD ["python", "services/app.py"]

