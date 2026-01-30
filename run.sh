#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${BLUE}[Message Board]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python() {
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.7 or higher."
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ $PYTHON_MAJOR -lt 3 ] || ([ $PYTHON_MAJOR -eq 3 ] && [ $PYTHON_MINOR -lt 7 ]); then
        print_error "Python 3.7 or higher is required. Found version $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION found"
}

# Function to setup virtual environment
setup_venv() {
    if [ ! -d "venv" ]; then
        print_message "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
        
        if [ $? -ne 0 ]; then
            print_error "Failed to create virtual environment"
            exit 1
        fi
        
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        print_error "Could not activate virtual environment"
        exit 1
    fi
    
    print_success "Virtual environment activated"
}

# Function to install dependencies
install_dependencies() {
    print_message "Checking dependencies..."
    
    # Check if pip is installed
    if ! command_exists pip; then
        print_message "Installing pip..."
        $PYTHON_CMD -m ensurepip --upgrade
    fi
    
    # Upgrade pip
    pip install --upgrade pip --quiet
    
    # Install Flask and Flask-CORS
    print_message "Installing required packages..."
    pip install flask flask-cors --quiet
    
    if [ $? -ne 0 ]; then
        print_error "Failed to install required packages"
        exit 1
    fi
    
    print_success "All dependencies installed"
}

# Function to check and install bore
check_and_install_bore() {
    print_message "Checking for bore.pub..."
    
    if command_exists bore; then
        print_success "bore.pub is installed"
        return 0
    fi
    
    print_warning "bore.pub is not installed"
    
    # Check for cargo
    if ! command_exists cargo; then
        print_error "cargo is not installed. Please install Rust to get cargo."
        print_message "Install Rust from: http://rustup.rs/"
        print_message "Then run: cargo install bore-cli"
        exit 1
    fi
    
    # Ask to install
    read -p "Install bore.pub now? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "bore.pub is required for sharing. Exiting."
        exit 1
    fi
    
    print_message "Installing bore.pub..."
    cargo install bore-cli
    
    if [ $? -ne 0 ]; then
        print_error "Failed to install bore.pub"
        exit 1
    fi
    
    # Verify installation
    if command_exists bore; then
        print_success "bore.pub installed successfully"
        return 0
    else
        print_error "bore.pub installation failed"
        exit 1
    fi
}

# Function to extract bore URL from output
extract_bore_url() {
    # Wait for bore to output URL (it appears after "listening at bore.pub:")
    sleep 3
    
    # Try multiple ways to get the URL
    # 1. Check if bore created a URL file (some versions do this)
    if [ -f "bore_url.txt" ]; then
        BORE_URL=$(cat bore_url.txt)
        rm -f bore_url.txt
        echo "$BORE_URL"
        return 0
    fi
    
    # 2. Try to get from bore status (newer versions)
    if command_exists bore && bore status 2>/dev/null | grep -q "bore.pub"; then
        bore status 2>/dev/null | grep -o "http://[a-zA-Z0-9.-]*\.bore\.pub"
        return 0
    fi
    
    # 3. Look for URL in recent terminal output (capture it)
    return 1
}

# Function to start bore tunnel
start_bore_tunnel() {
    local port=$1
    
    print_message "Starting bore.pub tunnel on port $port..."
    
    # Kill any existing bore processes on this port
    pkill -f "bore local $port" 2>/dev/null || true
    
    # Start bore and capture its output
    BORE_OUTPUT=$(mktemp)
    
    # Start bore in background, redirect output to file
    bore local $port --to bore.pub > "$BORE_OUTPUT" 2>&1 &
    BORE_PID=$!
    
    # Give bore time to start
    sleep 4
    
    # Check if bore process is still running
    if ! ps -p $BORE_PID > /dev/null 2>&1; then
        print_error "bore.pub failed to start. Check output:"
        cat "$BORE_OUTPUT"
        rm -f "$BORE_OUTPUT"
        exit 1
    fi
    
    # Extract URL from bore output
    BORE_URL=$(grep -o "http://[a-zA-Z0-9.-]*\.bore\.pub" "$BORE_OUTPUT" | head -1)
    
    if [ -z "$BORE_URL" ]; then
        # Try alternative pattern
        BORE_URL=$(grep -o "bore\.pub:[0-9]*" "$BORE_OUTPUT" | head -1)
        if [ -n "$BORE_URL" ]; then
            BORE_URL="http://$BORE_URL"
        fi
    fi
    
    # Clean up temp file
    rm -f "$BORE_OUTPUT"
    
    if [ -z "$BORE_URL" ]; then
        print_warning "Could not extract bore.pub URL from output"
        print_message "The tunnel is running (PID: $BORE_PID), but URL extraction failed."
        print_message "You can check the URL manually by looking at bore's output."
        print_message "Server is running locally at: http://localhost:$port"
        return 1
    fi
    
    print_success "bore.pub tunnel established!"
    echo ""
    echo "========================================"
    echo "🌐 Public URL: $BORE_URL"
    echo "🌐 Room link: ${BORE_URL}?room=main"
    echo "========================================"
    echo ""
    print_message "Share the above URL with anyone to chat!"
    print_message "Local access: http://localhost:$port"
    echo ""
    
    # Save URL to file for reference
    echo "$BORE_URL" > bore_current_url.txt
    print_message "URL saved to: bore_current_url.txt"
    
    return 0
}

# Function to choose server version
choose_server() {
    clear
    echo "========================================"
    echo "     🚀 Message Board Launcher"
    echo "========================================"
    echo ""
    echo "Choose your server version:"
    echo ""
	echo "1. Normal Version (Recommended)"
    echo "   - Clean, minimal interface"
    echo "   - Fast and lightweight"
    echo ""
    echo "2. Fancy Version"
    echo "   - Cosmic background with blinking stars"
    echo "   - Transparent glass-morphism UI"
    echo "   - Same features as normal version"
    echo ""
    echo "========================================"
    
    while true; do
        read -p "Enter your choice (1 or 2): " choice
        case $choice in
            1)
                SERVER_FILE="server.py"
                SERVER_NAME="Normal Version"
                return 0
                ;;
            2)
                SERVER_FILE="server_fancy.py"
                SERVER_NAME="Fancy Version"
                return 0
                ;;
            *)
                print_error "Invalid choice. Please enter 1 or 2."
                ;;
        esac
    done
}

# Function to check if server file exists
check_server_file() {
    if [ ! -f "$SERVER_FILE" ]; then
        print_error "$SERVER_FILE not found!"
        print_message "Make sure you're in the correct directory."
        print_message "Expected files: server.py and server_fancy.py"
        exit 1
    fi
}

# Function to start server
start_server() {
    local port=5000
    
    print_message "Starting $SERVER_NAME on port $port..."
    
    # Start the server in background
    python "$SERVER_FILE" &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 3
    
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        print_success "Server started successfully!"
    else
        print_error "Failed to start server"
        exit 1
    fi
    
    # Start bore tunnel
    if start_bore_tunnel $port; then
        print_message "Press Ctrl+C to stop both server and tunnel"
        
        # Wait for user interrupt
        wait $BORE_PID 2>/dev/null || true
    else
        print_message "Server running locally at: http://localhost:$port"
        print_message "Press Ctrl+C to stop the server"
        wait $SERVER_PID
    fi
}

# Cleanup function
cleanup() {
    echo ""
    print_message "Shutting down..."
    
    # Kill server if running
    if [ -n "$SERVER_PID" ] && ps -p $SERVER_PID > /dev/null 2>&1; then
        kill $SERVER_PID 2>/dev/null
        print_success "Server stopped"
    fi
    
    # Kill bore if running
    if [ -n "$BORE_PID" ] && ps -p $BORE_PID > /dev/null 2>&1; then
        kill $BORE_PID 2>/dev/null
        print_success "bore.pub tunnel stopped"
    fi
    
    # Clean up URL file
    rm -f bore_current_url.txt
    
    # Deactivate virtual environment
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate 2>/dev/null
        print_success "Virtual environment deactivated"
    fi
    
    exit 0
}

# Trap Ctrl+C for cleanup
trap cleanup INT TERM

# Main execution
main() {
    # Check Python
    check_python
    
    # Setup virtual environment
    setup_venv
    
    # Install dependencies
    install_dependencies
    
    # Check and install bore
    check_and_install_bore
    
    # Choose server version
    choose_server
    
    # Check if server file exists
    check_server_file
    
    # Start server
    start_server
}

# Run main function
main
