
    mkdir -p ~/AskDoc-AI
    cd ~/AskDoc-AI
    tar -xzf ~/deploy.tar.gz
    
    # Install docker if not present
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        sudo apt update
        sudo apt install -y docker.io docker-compose-v2
        sudo systemctl enable --now docker
        sudo usermod -aG docker $USER
    fi
    
    echo "Running Docker Compose..."
    sudo docker compose up -d --build
    