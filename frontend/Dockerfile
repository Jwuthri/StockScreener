FROM node:16-alpine

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies with specific settings to avoid the ajv error
RUN npm install --legacy-peer-deps
RUN npm install ajv@^6.12.3 ajv-keywords@^3.5.2

# Copy all files
COPY . .

# Start the app
CMD ["npm", "start"]
