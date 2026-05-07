---
name: node-js-installation
version: 1.0
description: Skill for installing and managing Node.js, including handling version conflicts.
---

# Node.js Installation Skill

## Goal
Guide users through installing Node.js and managing version control, ensuring an appropriate setup for development environments.

## Instructions
1. **Download Node.js LTS**:
   - Visit [Node.js official site](https://nodejs.org/en/download/) and download the latest LTS version suitable for your operating system.

2. **Linux Users**:
   - For Debian-based systems, use the following commands:
     ```bash
     sudo apt update
     sudo apt install nodejs npm
     ```

3. **Verify Installation**:
   - To check your Node.js version, run:
     ```bash
     node -v
     ```

## Notes
- Always verify the success or presence of existing services on your target port before launching a new service to prevent conflicts.
- Use Node Version Manager (nvm) for easier handling of multiple Node.js versions. You can install it by following the instructions at the [nvm repository](https://github.com/nvm-sh/nvm).
- Use commands like `nvm install <version>` to switch versions efficiently.

## Update log
- Created when encountering issues related to port conflicts and Node.js installation errors during a project setup.
