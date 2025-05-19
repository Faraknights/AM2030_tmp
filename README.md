# AM2030 Prototype Setup

## 1. **Build the Docker Image**

To build the Docker image from the `Dockerfile` in the current directory, run:

``docker build -t prototype_am2030_gpu .``

This command will create the image `prototype_am2030_gpu`.

## 2. **Run the Docker Container on GPU**

Once the image is built, run the container with GPU support and map port 5000 from the container to the host:

``docker run --gpus all -d -p 5000:5000 --name am2030_prototype prototype_am2030_gpu``

This will:

- Start the container in detached mode (`-d`).
- Give the container access to all GPUs (`--gpus all`).
- Expose port 5000 to the host, making the Flask app accessible.

## 3. **Access the prototype UI**

Once the container is running, you can access the Flask app UI in your browser at:

```
http://localhost:5000
```

You can also use `curl` to interact with the application via its endpoints.

## 4. **Stopping the Container**

To stop the container, use the following command:

``docker stop am2030_prototype``

To remove the container:

``docker rm am2030_prototype``
