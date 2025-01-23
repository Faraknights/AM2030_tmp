# Use Node.js image
FROM node:20

# Set working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json first to optimize layer caching
COPY react-ui/package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application files
COPY react-ui/ .

# Expose the React development server port
EXPOSE 3000

# Start the React app
CMD ["npm", "start"]
