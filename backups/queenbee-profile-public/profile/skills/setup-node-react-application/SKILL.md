---
name: setup-node-react-application
category: web-development
description: Steps for setting up a Node.js backend and a React frontend for a dog grooming business application.
---

# Skill for Setting Up a Node.js Backend and React Frontend

## Overview
This skill outlines the steps to set up a Node.js backend and a React frontend for a business application, specifically tailored for a dog grooming service.

## Steps
1. **Install Node.js and Required Packages**:
   - Use Node Version Manager (nvm) or download directly.
   - Install core packages:
     ```bash
     npm install express mongoose body-parser cors
     ```

2. **Set Up a Basic Express Server**:
   - Create `server.js` and establish a MongoDB connection.
   - Define routes for handling requests.

3. **Create a React Application**:
   - Use Create React App to scaffold the frontend:
     ```bash
     npx create-react-app frontend
     ```
   - Install additional libraries, such as axios for API calls:
     ```bash
     npm install axios
     ```

4. **Handle Port Conflicts**:
   - Before starting the server, check if the desired port is in use:
     ```bash
     lsof -i :PORT_NUMBER
     ```
   - Change port if conflicts are detected.

5. **Apply Environment Variables**:
   - If encountering compatibility issues, set necessary environment variables:
     ```bash
     export NODE_OPTIONS=--openssl-legacy-provider
     ```

6. **Run the Applications**:
   - Start the backend server and frontend:
     ```bash
     node server.js
     npm start
     ```

## Notes
- Always verify the environment and installed versions of Node.js and libraries to prevent compatibility issues. This process may require trial and error to ensure the setup is stable.
