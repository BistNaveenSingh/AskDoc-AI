# EC2 Deployment Guide

Follow these steps to deploy **AskDoc AI** to an AWS EC2 instance using Docker Compose.

## 1. Launch an EC2 Instance
1. Go to your AWS Console and launch an EC2 instance.
2. Select **Ubuntu Server 22.04 LTS** (or 24.04).
3. Select an Instance Type (e.g., `t2.medium` or `t3.medium` is recommended as FAISS and LLM libraries can be a bit heavy on RAM, but `t2.micro` might work for testing).
4. In the **Security Group** settings, allow the following inbound traffic:
   - **SSH (Port 22)**: From your IP.
   - **Custom TCP (Port 8501)**: Anywhere (0.0.0.0/0) - *This is for the Streamlit UI.*
   - **Custom TCP (Port 8000)**: Anywhere (0.0.0.0/0) - *This is for the FastAPI backend (optional, only if you want to access the API directly).*

## 2. SSH into your Instance
Open your terminal and connect using your `.pem` key:
```bash
ssh -i /path/to/your-key.pem ubuntu@<YOUR-EC2-PUBLIC-IP>
```

## 3. Install Docker and Docker Compose
Run the following commands on your EC2 instance to install Docker:
```bash
# Update packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y docker.io docker-compose

# Add the ubuntu user to the docker group so you don't have to use 'sudo' every time
sudo usermod -aG docker ubuntu
```
*(You may need to log out of the SSH session and log back in for the group change to take effect).*

## 4. Get Your Code on the Server
You can either use `git clone` to pull your code from GitHub, or use `scp` to copy your local folder to the server.

If using GitHub:
```bash
git clone https://github.com/your-username/AntiRag.git
cd AntiRag
```

## 5. Set up Environment Variables
You need to create your `.env` file on the server.
```bash
nano .env
```
Paste your `OPENAI_API_KEY` into this file:
```
OPENAI_API_KEY=sk-proj-your-key-here
```
Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

## 6. Start the Application
Run the following command in the `AntiRag` directory where your `docker-compose.yml` is located:
```bash
docker-compose up -d --build
```
This command will:
1. Build the API and UI images from your code.
2. Start the containers in the background (`-d`).

## 7. Access Your App
Once the containers are running, open your web browser and go to:
```
http://<YOUR-EC2-PUBLIC-IP>:8501
```

You should see your AskDoc AI app live!

### Helpful Docker Commands
- **Check logs:** `docker-compose logs -f`
- **Stop the app:** `docker-compose down`
- **Restart the app (after code changes):** `docker-compose up -d --build`
