# Installing Redis on Ubuntu

This guide will walk you through the steps to install and configure Redis on an Ubuntu system.

## Prerequisites

- An Ubuntu system (e.g., Ubuntu 20.04 or later)
- A user account with `sudo` privileges

## Installation Steps

1. **Update your package list and install Redis**

   Begin by updating your package list to ensure you have the latest version information. Then, install the Redis server package:

   ```bash
   sudo apt update
   sudo apt install redis-server

2. **Start the Redis server**
   ```bash
   sudo systemctl start redis-server

3. **Enable Redis to start on boot**

     ```bash
     sudo systemctl enable redis-server
  
   



