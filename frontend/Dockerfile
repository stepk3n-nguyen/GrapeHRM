FROM node:20-alpine

WORKDIR /app

# Copy package dependencies
COPY package.json ./

# Install npm packages
RUN npm install

# Copy application source
COPY . .

# Expose Vite dev server port
EXPOSE 3000

# Start Vite dev server with host binding
CMD ["npm", "run", "dev"]
