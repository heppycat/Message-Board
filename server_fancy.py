from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)

# Store messages and user info
messages = {}
user_info = {}

# Available colors for users to choose from
AVAILABLE_COLORS = [
    '#1a73e8',  # Blue
    '#34a853',  # Green
    '#ea4335',  # Red
    '#fbbc04',  # Yellow/Orange
    '#8e44ad',  # Purple
    '#16a085',  # Teal
    '#e74c3c',  # Light Red
    '#3498db',  # Light Blue
    '#2ecc71',  # Emerald
    '#e67e22',  # Dark Orange
    '#9b59b6',  # Violet
    '#1abc9c',  # Turquoise
]

# Available avatar shapes
AVATAR_SHAPES = ['square', 'circle', 'diamond']

def get_user_info(user_id):
    """Get or create user info with random color and default settings"""
    if user_id not in user_info:
        # Assign a color based on user index
        color_index = len(user_info) % len(AVAILABLE_COLORS)
        default_color = AVAILABLE_COLORS[color_index]
        default_name = f'User{len(user_info) + 1}'
        user_info[user_id] = {
            'color': default_color,
            'name': default_name,
            'shape': 'square'  # Default shape
        }
    return user_info[user_id]

# Ultra-minimal dark theme with cosmic background
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Message Board</title>
    <style>
        :root {
            --bg: #000000;
            --bg-light: rgba(17, 17, 17, 0.7);
            --bg-transparent: rgba(17, 17, 17, 0.5);
            --border: rgba(34, 34, 34, 0.8);
            --text: #ffffff;
            --text-light: #888888;
            --accent: #1a73e8;
            --accent-hover: #0d62d9;
            --glass: rgba(0, 0, 0, 0.2);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            height: 100vh;
            overflow: hidden;
            position: relative;
        }
        
        /* Cosmic background with stars */
        #stars {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
        }
        
        .star {
            position: absolute;
            background-color: white;
            border-radius: 50%;
            animation: twinkle var(--duration) infinite ease-in-out;
        }
        
        @keyframes twinkle {
            0%, 100% { opacity: 0.1; transform: scale(0.8); }
            50% { opacity: 1; transform: scale(1.2); }
        }
        
        #app {
            height: 100vh;
            display: flex;
            flex-direction: column;
            max-width: 800px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }
        
        .header {
            padding: 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            background: var(--glass);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
        
        .header h1 {
            font-size: 20px;
            font-weight: 600;
            white-space: nowrap;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .user-avatar {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(5px);
        }
        
        .user-avatar:hover {
            opacity: 0.9;
            border-color: var(--text-light);
        }
        
        .user-avatar.circle {
            border-radius: 50%;
        }
        
        .user-avatar.diamond {
            border-radius: 4px;
            transform: rotate(45deg);
        }
        
        .user-avatar.diamond span {
            transform: rotate(-45deg);
        }
        
        .user-name {
            font-size: 14px;
            color: var(--text-light);
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
            transition: background 0.2s;
        }
        
        .user-name:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        .status {
            font-size: 12px;
            color: var(--text-light);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .status::before {
            content: '';
            width: 6px;
            height: 6px;
            background: #34a853;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .message {
            display: flex;
            gap: 12px;
            opacity: 0;
            animation: fadeIn 0.2s ease forwards;
        }
        
        @keyframes fadeIn {
            to { opacity: 1; }
        }
        
        .avatar {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            backdrop-filter: blur(5px);
            background: rgba(255, 255, 255, 0.1);
        }
        
        .avatar.circle {
            border-radius: 50%;
        }
        
        .avatar.diamond {
            border-radius: 4px;
            transform: rotate(45deg);
        }
        
        .avatar.diamond span {
            transform: rotate(-45deg);
        }
        
        .content {
            flex: 1;
        }
        
        .meta {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }
        
        .sender {
            font-weight: 500;
            font-size: 14px;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
        }
        
        .time {
            font-size: 12px;
            color: var(--text-light);
        }
        
        .text {
            font-size: 15px;
            line-height: 1.4;
            background: var(--bg-transparent);
            padding: 12px 16px;
            border-radius: 12px;
            border: 1px solid var(--border);
            backdrop-filter: blur(5px);
        }
        
        .input-area {
            padding: 20px;
            border-top: 1px solid var(--border);
            background: var(--glass);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
        
        .input-wrapper {
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }
        
        textarea {
            flex: 1;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px 16px;
            color: var(--text);
            font-size: 15px;
            font-family: inherit;
            resize: none;
            line-height: 1.4;
            min-height: 44px;
            max-height: 120px;
            outline: none;
            transition: all 0.15s;
            backdrop-filter: blur(5px);
        }
        
        textarea:focus {
            border-color: var(--accent);
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 0 0 1px var(--accent);
        }
        
        textarea::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }
        
        button {
            background: var(--accent);
            color: white;
            border: none;
            width: 36px;
            height: 36px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.15s;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(5px);
        }
        
        button:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
        }
        
        button:disabled {
            background: rgba(34, 34, 34, 0.5);
            cursor: not-allowed;
            transform: none;
        }
        
        .share {
            padding: 12px 20px;
            border-top: 1px solid var(--border);
            font-size: 13px;
            color: var(--text-light);
            background: var(--glass);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
        
        .url {
            display: flex;
            gap: 8px;
            margin-top: 6px;
        }
        
        .url span {
            background: rgba(255, 255, 255, 0.1);
            padding: 8px 12px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 12px;
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            backdrop-filter: blur(5px);
            border: 1px solid var(--border);
        }
        
        .url button {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-light);
            font-size: 12px;
            width: auto;
            height: auto;
            padding: 6px 12px;
        }
        
        .url button:hover {
            background: rgba(255, 255, 255, 0.1);
            color: var(--text);
        }
        
        .empty {
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-light);
            font-size: 14px;
            background: var(--bg-transparent);
            border-radius: 12px;
            margin: 20px;
            padding: 40px;
            backdrop-filter: blur(5px);
            border: 1px solid var(--border);
        }
        
        /* Modal for user settings */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s;
            backdrop-filter: blur(5px);
        }
        
        .modal-overlay.visible {
            opacity: 1;
            visibility: visible;
        }
        
        .modal {
            background: rgba(0, 0, 0, 0.9);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            width: 90%;
            max-width: 400px;
            transform: translateY(20px);
            transition: transform 0.3s;
            backdrop-filter: blur(10px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        }
        
        .modal-overlay.visible .modal {
            transform: translateY(0);
        }
        
        .modal h2 {
            font-size: 18px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .modal label {
            display: block;
            font-size: 14px;
            margin-bottom: 8px;
            color: var(--text-light);
        }
        
        .modal input {
            width: 100%;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            color: var(--text);
            font-size: 15px;
            margin-bottom: 20px;
            outline: none;
            backdrop-filter: blur(5px);
        }
        
        .modal input:focus {
            border-color: var(--accent);
            background: rgba(255, 255, 255, 0.15);
        }
        
        .color-picker, .shape-picker {
            margin-bottom: 20px;
        }
        
        .color-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 8px;
            margin-top: 8px;
        }
        
        .color-option {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            cursor: pointer;
            transition: transform 0.2s, border-color 0.2s;
            border: 2px solid transparent;
            backdrop-filter: blur(5px);
        }
        
        .color-option:hover {
            transform: scale(1.1);
        }
        
        .color-option.selected {
            border-color: white;
            transform: scale(1.1);
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
        }
        
        .shape-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-top: 8px;
        }
        
        .shape-option {
            width: 32px;
            height: 32px;
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid var(--border);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            backdrop-filter: blur(5px);
        }
        
        .shape-option:hover {
            border-color: var(--accent);
            transform: scale(1.1);
        }
        
        .shape-option.selected {
            border-color: var(--accent);
            background: rgba(26, 115, 232, 0.2);
            transform: scale(1.1);
            box-shadow: 0 0 10px rgba(26, 115, 232, 0.3);
        }
        
        .shape-option.circle {
            border-radius: 50%;
        }
        
        .shape-option.diamond {
            border-radius: 4px;
            transform: rotate(45deg) scale(1);
        }
        
        .shape-option.diamond:hover {
            transform: rotate(45deg) scale(1.1);
        }
        
        .shape-option.selected.diamond {
            transform: rotate(45deg) scale(1.1);
        }
        
        .modal-buttons {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
            margin-top: 10px;
        }
        
        .modal-buttons button {
            width: auto;
            height: auto;
            padding: 8px 16px;
            border-radius: 8px;
        }
        
        .modal-buttons .cancel {
            background: rgba(255, 255, 255, 0.1);
            color: var(--text);
        }
        
        .modal-buttons .cancel:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        /* Hide scrollbar for Chrome, Safari and Opera */
        .messages::-webkit-scrollbar {
            display: none;
        }
        
        /* Hide scrollbar for IE, Edge and Firefox */
        .messages {
            -ms-overflow-style: none;
            scrollbar-width: none;
        }
        
        /* Smooth scrolling */
        .messages {
            scroll-behavior: smooth;
        }
        
        /* Glass effect for messages container */
        .messages::before {
            content: '';
            position: fixed;
            top: 80px;
            left: 0;
            right: 0;
            height: calc(100vh - 200px);
            background: linear-gradient(
                to bottom,
                transparent,
                rgba(0, 0, 0, 0.3) 20%,
                rgba(0, 0, 0, 0.3) 80%,
                transparent
            );
            pointer-events: none;
            z-index: -1;
        }
    </style>
</head>
<body>
    <div id="stars"></div>
    
    <div id="app">
        <div class="header">
            <h1>Message Board</h1>
            <div class="user-info">
                <div class="user-avatar" id="userAvatar" onclick="showSettingsModal()">
                    <span>ME</span>
                </div>
                <div class="user-name" onclick="showSettingsModal()" id="userName">User</div>
            </div>
            <div class="status">Online</div>
        </div>
        
        <div class="messages" id="messages">
            <!-- Messages appear here -->
        </div>
        
        <div class="input-area">
            <div class="input-wrapper">
                <textarea 
                    id="input" 
                    placeholder="Type a message..."
                    rows="1"
                    autofocus
                ></textarea>
                <button id="send" onclick="sendMessage()">
                    →
                </button>
            </div>
        </div>
        
        <div class="share">
            Share this link:
            <div class="url">
                <span id="shareUrl">Loading...</span>
                <button onclick="copyLink()">Copy</button>
            </div>
        </div>
        
        <!-- Settings Modal -->
        <div class="modal-overlay" id="settingsModal">
            <div class="modal">
                <h2>Your Profile</h2>
                
                <label for="nameInput">Display Name</label>
                <input 
                    type="text" 
                    id="nameInput" 
                    placeholder="Enter your name"
                    maxlength="20"
                >
                
                <div class="color-picker">
                    <label>Color</label>
                    <div class="color-grid" id="colorGrid">
                        <!-- Colors will be added here -->
                    </div>
                </div>
                
                <div class="shape-picker">
                    <label>Avatar Shape</label>
                    <div class="shape-grid" id="shapeGrid">
                        <!-- Shapes will be added here -->
                    </div>
                </div>
                
                <div class="modal-buttons">
                    <button class="cancel" onclick="hideSettingsModal()">Cancel</button>
                    <button onclick="saveSettings()">Save</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Available colors (must match server's colors)
        const AVAILABLE_COLORS = [
            '#1a73e8', '#34a853', '#ea4335', '#fbbc04', '#8e44ad', '#16a085',
            '#e74c3c', '#3498db', '#2ecc71', '#e67e22', '#9b59b6', '#1abc9c'
        ];
        
        // Available avatar shapes
        const AVATAR_SHAPES = ['square', 'circle', 'diamond'];
        
        // Generate unique user ID
        const userId = 'user-' + Math.random().toString(36).substr(2, 9);
        let userColor = AVAILABLE_COLORS[0];
        let userName = 'User';
        let userShape = 'square';
        let lastMessageId = null;
        let isAtBottom = true;
        
        // Create cosmic background with stars
        function createStars() {
            const starsContainer = document.getElementById('stars');
            const starCount = 150;
            
            for (let i = 0; i < starCount; i++) {
                const star = document.createElement('div');
                star.className = 'star';
                
                // Random position
                const x = Math.random() * 100;
                const y = Math.random() * 100;
                
                // Random size (very small to small)
                const size = Math.random() * 2 + 0.5;
                
                // Random twinkle duration
                const duration = Math.random() * 3 + 2;
                
                // Random delay
                const delay = Math.random() * 5;
                
                // Apply styles
                star.style.left = `${x}%`;
                star.style.top = `${y}%`;
                star.style.width = `${size}px`;
                star.style.height = `${size}px`;
                star.style.setProperty('--duration', `${duration}s`);
                star.style.animationDelay = `${delay}s`;
                
                // Random opacity
                star.style.opacity = Math.random() * 0.5 + 0.1;
                
                starsContainer.appendChild(star);
            }
        }
        
        // Load user info from localStorage
        function loadUserInfo() {
            const savedName = localStorage.getItem('messageBoard_userName');
            const savedColor = localStorage.getItem('messageBoard_userColor');
            const savedShape = localStorage.getItem('messageBoard_userShape');
            
            if (savedName) {
                userName = savedName;
                document.getElementById('userName').textContent = userName;
            }
            
            if (savedColor && AVAILABLE_COLORS.includes(savedColor)) {
                userColor = savedColor;
            } else {
                // Assign a color based on user ID hash
                const hash = userId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
                userColor = AVAILABLE_COLORS[hash % AVAILABLE_COLORS.length];
                localStorage.setItem('messageBoard_userColor', userColor);
            }
            
            if (savedShape && AVATAR_SHAPES.includes(savedShape)) {
                userShape = savedShape;
            } else {
                localStorage.setItem('messageBoard_userShape', userShape);
            }
            
            // Update avatar
            updateAvatar();
            
            // Send user info to server
            updateUserInfo();
        }
        
        // Update avatar display
        function updateAvatar() {
            const avatarEl = document.getElementById('userAvatar');
            const initials = userName.substring(0, 2).toUpperCase();
            
            // Update text
            avatarEl.innerHTML = `<span>${initials}</span>`;
            
            // Update color
            avatarEl.style.background = userColor;
            
            // Update shape classes - remove all shape classes first
            avatarEl.className = 'user-avatar';
            if (userShape !== 'square') {
                avatarEl.classList.add(userShape);
            }
        }
        
        // Send user info to server
        async function updateUserInfo() {
            try {
                await fetch('/user', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: userId,
                        name: userName,
                        color: userColor,
                        shape: userShape
                    })
                });
            } catch (error) {
                console.error('Failed to update user info:', error);
            }
        }
        
        // Get room from URL
        function getRoom() {
            const params = new URLSearchParams(window.location.search);
            let room = params.get('room');
            if (!room) {
                room = 'main';
                history.replaceState({}, '', `?room=${room}`);
            }
            return room;
        }
        
        const room = getRoom();
        const messagesEl = document.getElementById('messages');
        const inputEl = document.getElementById('input');
        const sendBtn = document.getElementById('send');
        const shareUrlEl = document.getElementById('shareUrl');
        const settingsModal = document.getElementById('settingsModal');
        const nameInput = document.getElementById('nameInput');
        const colorGrid = document.getElementById('colorGrid');
        const shapeGrid = document.getElementById('shapeGrid');
        
        // Initialize
        createStars();
        loadUserInfo();
        shareUrlEl.textContent = location.origin + location.pathname + '?room=' + room;
        
        // Populate color grid
        function populateColorGrid() {
            colorGrid.innerHTML = '';
            AVAILABLE_COLORS.forEach(color => {
                const div = document.createElement('div');
                div.className = 'color-option';
                div.style.background = color;
                div.dataset.color = color;
                
                if (color === userColor) {
                    div.classList.add('selected');
                }
                
                div.addEventListener('click', () => {
                    // Remove selected from all colors
                    document.querySelectorAll('.color-option').forEach(el => {
                        el.classList.remove('selected');
                    });
                    // Add selected to clicked color
                    div.classList.add('selected');
                });
                
                colorGrid.appendChild(div);
            });
        }
        
        // Populate shape grid
        function populateShapeGrid() {
            shapeGrid.innerHTML = '';
            AVATAR_SHAPES.forEach(shape => {
                const div = document.createElement('div');
                div.className = `shape-option ${shape}`;
                div.dataset.shape = shape;
                div.title = shape.charAt(0).toUpperCase() + shape.slice(1);
                
                if (shape === userShape) {
                    div.classList.add('selected');
                }
                
                div.addEventListener('click', () => {
                    // Remove selected from all shapes
                    document.querySelectorAll('.shape-option').forEach(el => {
                        el.classList.remove('selected');
                    });
                    // Add selected to clicked shape
                    div.classList.add('selected');
                });
                
                shapeGrid.appendChild(div);
            });
        }
        
        // Settings modal functions
        function showSettingsModal() {
            nameInput.value = userName;
            populateColorGrid();
            populateShapeGrid();
            settingsModal.classList.add('visible');
            nameInput.focus();
        }
        
        function hideSettingsModal() {
            settingsModal.classList.remove('visible');
        }
        
        async function saveSettings() {
            const newName = nameInput.value.trim();
            const selectedColorEl = document.querySelector('.color-option.selected');
            const selectedShapeEl = document.querySelector('.shape-option.selected');
            
            const newColor = selectedColorEl ? selectedColorEl.dataset.color : userColor;
            const newShape = selectedShapeEl ? selectedShapeEl.dataset.shape : userShape;
            
            let changed = false;
            
            if (newName && newName !== userName) {
                userName = newName;
                document.getElementById('userName').textContent = userName;
                localStorage.setItem('messageBoard_userName', userName);
                changed = true;
            }
            
            if (newColor !== userColor) {
                userColor = newColor;
                localStorage.setItem('messageBoard_userColor', userColor);
                changed = true;
            }
            
            if (newShape !== userShape) {
                userShape = newShape;
                localStorage.setItem('messageBoard_userShape', userShape);
                changed = true;
            }
            
            if (changed) {
                // Update avatar
                updateAvatar();
                
                // Notify server
                await updateUserInfo();
                
                // Reload messages to show new settings
                await loadMessages();
            }
            
            hideSettingsModal();
        }
        
        // Auto-resize textarea
        inputEl.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            sendBtn.disabled = this.value.trim() === '';
        });
        
        // Send on Enter (without Shift)
        inputEl.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (this.value.trim()) {
                    sendMessage();
                }
            }
        });
        
        // Modal enter key
        nameInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                saveSettings();
            } else if (e.key === 'Escape') {
                hideSettingsModal();
            }
        });
        
        // Track scroll position
        messagesEl.addEventListener('scroll', function() {
            const { scrollTop, scrollHeight, clientHeight } = this;
            isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
        });
        
        // Smart message rendering - only update if needed
        async function updateMessages() {
            try {
                const res = await fetch(`/messages?room=${room}&since=${lastMessageId || ''}`);
                const newMessages = await res.json();
                
                if (newMessages.length === 0) return;
                
                // Find the last message that's already displayed
                const existingIds = new Set(
                    Array.from(messagesEl.children)
                        .map(el => el.dataset.id)
                        .filter(id => id)
                );
                
                // Add only new messages
                const messagesToAdd = newMessages.filter(msg => !existingIds.has(msg.id));
                
                if (messagesToAdd.length === 0) return;
                
                // Add new messages
                messagesToAdd.forEach(msg => {
                    const time = formatTime(msg.timestamp);
                    const isMe = msg.sender_id === userId;
                    const color = msg.sender_color;
                    const name = msg.sender_name || 'User';
                    const shape = msg.sender_shape || 'square';
                    const initials = name.substring(0, 2).toUpperCase();
                    
                    const div = document.createElement('div');
                    div.className = 'message';
                    div.dataset.id = msg.id;
                    
                    // Create avatar with shape
                    let avatarHTML = '';
                    let avatarClass = 'avatar';
                    if (shape === 'circle') {
                        avatarClass += ' circle';
                    } else if (shape === 'diamond') {
                        avatarClass += ' diamond';
                    }
                    
                    avatarHTML = `<div class="${avatarClass}" style="background: ${color}"><span>${initials}</span></div>`;
                    
                    div.innerHTML = `
                        ${avatarHTML}
                        <div class="content">
                            <div class="meta">
                                <span class="sender" style="color: ${color}">${isMe ? 'You' : name}</span>
                                <span class="time">${time}</span>
                            </div>
                            <div class="text">${escapeHtml(msg.text)}</div>
                        </div>
                    `;
                    
                    messagesEl.appendChild(div);
                    
                    // Update last message ID
                    lastMessageId = msg.id;
                });
                
                // Scroll to bottom if user was already there
                if (isAtBottom) {
                    messagesEl.scrollTop = messagesEl.scrollHeight;
                }
                
            } catch (error) {
                console.error('Update failed:', error);
            }
        }
        
        // Initial load
        async function loadMessages() {
            try {
                const res = await fetch(`/messages?room=${room}`);
                const allMessages = await res.json();
                
                if (allMessages.length === 0) {
                    messagesEl.innerHTML = '<div class="empty">No messages yet</div>';
                    return;
                }
                
                messagesEl.innerHTML = '';
                
                allMessages.forEach(msg => {
                    const time = formatTime(msg.timestamp);
                    const isMe = msg.sender_id === userId;
                    const color = msg.sender_color;
                    const name = msg.sender_name || 'User';
                    const shape = msg.sender_shape || 'square';
                    const initials = name.substring(0, 2).toUpperCase();
                    
                    const div = document.createElement('div');
                    div.className = 'message';
                    div.dataset.id = msg.id;
                    
                    // Create avatar with shape
                    let avatarHTML = '';
                    let avatarClass = 'avatar';
                    if (shape === 'circle') {
                        avatarClass += ' circle';
                    } else if (shape === 'diamond') {
                        avatarClass += ' diamond';
                    }
                    
                    avatarHTML = `<div class="${avatarClass}" style="background: ${color}"><span>${initials}</span></div>`;
                    
                    div.innerHTML = `
                        ${avatarHTML}
                        <div class="content">
                            <div class="meta">
                                <span class="sender" style="color: ${color}">${isMe ? 'You' : name}</span>
                                <span class="time">${time}</span>
                            </div>
                            <div class="text">${escapeHtml(msg.text)}</div>
                        </div>
                    `;
                    
                    messagesEl.appendChild(div);
                    lastMessageId = msg.id;
                });
                
                // Scroll to bottom
                messagesEl.scrollTop = messagesEl.scrollHeight;
                
            } catch (error) {
                console.error('Load failed:', error);
                messagesEl.innerHTML = '<div class="empty">Connection error</div>';
            }
        }
        
        // Send message
        async function sendMessage() {
            const text = inputEl.value.trim();
            if (!text) return;
            
            // Save original text and clear
            const originalText = text;
            inputEl.value = '';
            inputEl.style.height = 'auto';
            sendBtn.disabled = true;
            
            try {
                const res = await fetch('/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        room: room,
                        text: originalText,
                        sender_id: userId
                    })
                });
                
                if (!res.ok) throw new Error('Send failed');
                
                // Update messages immediately
                await updateMessages();
                
            } catch (error) {
                console.error('Send failed:', error);
                // Restore text if failed
                inputEl.value = originalText;
                inputEl.focus();
            }
            
            sendBtn.disabled = false;
            inputEl.focus();
        }
        
        // Copy link
        async function copyLink() {
            try {
                await navigator.clipboard.writeText(shareUrlEl.textContent);
                alert('Link copied!');
            } catch (error) {
                alert('Failed to copy');
            }
        }
        
        // Helper functions
        function formatTime(timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;
            
            if (diff < 60000) return 'Just now';
            if (diff < 3600000) return Math.floor(diff / 60000) + 'm';
            if (diff < 86400000) return Math.floor(diff / 3600000) + 'h';
            return date.getHours().toString().padStart(2, '0') + ':' + 
                   date.getMinutes().toString().padStart(2, '0');
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Initialize
        loadMessages();
        populateColorGrid();
        populateShapeGrid();
        
        // Smart polling - only update when needed
        let updateTimer = null;
        function scheduleUpdate() {
            if (updateTimer) clearTimeout(updateTimer);
            updateTimer = setTimeout(async () => {
                await updateMessages();
                scheduleUpdate();
            }, 1000);
        }
        
        scheduleUpdate();
        
        // Also update when window gets focus
        window.addEventListener('focus', updateMessages);
        
        // Auto-focus input
        inputEl.focus();
        
        // Close modal on overlay click
        settingsModal.addEventListener('click', function(e) {
            if (e.target === this) {
                hideSettingsModal();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/send', methods=['POST'])
def send_message():
    try:
        data = request.json
        room = data.get('room', 'main')
        text = data.get('text', '').strip()
        sender_id = data.get('sender_id', 'anonymous')
        
        if not text:
            return jsonify({'error': 'No message text'}), 400
        
        if room not in messages:
            messages[room] = []
        
        # Get user info - this will create it if it doesn't exist
        user_data = get_user_info(sender_id)
        
        message = {
            'id': str(uuid.uuid4()),
            'text': text,
            'sender_id': sender_id,
            'sender_color': user_data['color'],
            'sender_name': user_data['name'],
            'sender_shape': user_data['shape'],  # Include shape in message
            'timestamp': datetime.now().isoformat()
        }
        
        messages[room].append(message)
        
        # Keep only last 200 messages
        if len(messages[room]) > 200:
            messages[room] = messages[room][-200:]
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/user', methods=['POST'])
def update_user():
    try:
        data = request.json
        user_id = data.get('user_id')
        name = data.get('name', '').strip()
        color = data.get('color')
        shape = data.get('shape')
        
        if not user_id:
            return jsonify({'error': 'No user ID'}), 400
        
        # Validate color is in our available colors
        if color and color not in AVAILABLE_COLORS:
            return jsonify({'error': 'Invalid color'}), 400
        
        # Validate shape is valid
        if shape and shape not in AVATAR_SHAPES:
            return jsonify({'error': 'Invalid shape'}), 400
        
        # Get existing user info or create new
        if user_id in user_info:
            if name:
                user_info[user_id]['name'] = name[:20]
            if color:
                user_info[user_id]['color'] = color
            if shape:
                user_info[user_id]['shape'] = shape
        else:
            # Create new user with provided info or defaults
            if not color:
                color_index = len(user_info) % len(AVAILABLE_COLORS)
                color = AVAILABLE_COLORS[color_index]
            
            if not shape:
                shape = 'square'
            
            user_info[user_id] = {
                'color': color,
                'name': name[:20] if name else f'User{len(user_info) + 1}',
                'shape': shape
            }
        
        return jsonify({'success': True, 'user_info': user_info[user_id]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/messages')
def get_messages():
    room = request.args.get('room', 'main')
    since = request.args.get('since', None)
    
    room_messages = messages.get(room, [])
    
    # If since parameter provided, return only newer messages
    if since:
        try:
            index = next(i for i, msg in enumerate(room_messages) if msg['id'] == since)
            return jsonify(room_messages[index + 1:])
        except (StopIteration, ValueError):
            pass
    
    return jsonify(room_messages)

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 COSMIC MESSAGE BOARD")
    print("="*50)
    print("\n📍 Local: http://localhost:5000")
    print("\n🔗 To share with friends (using bore.pub):")
    print("   1. Install bore.pub")
    print("   2. In a NEW terminal, expose your port:")
    print("      bore local 5000 --to bore.pub")
    print("   3. bore.pub will give you a public URL like:")
    print("      https://bore.pub:12345")
    print("   4. Send that URL to anyone!")
    print("\n🌌 Features:")
    print("   • Blinking stars in deep black cosmic background")
    print("   • Transparent glass-morphism UI elements")
    print("   • Backdrop blur effects throughout")
    print("\n🎨 Personalization:")
    print("   • Choose avatar shape: Square, Circle, or Diamond")
    print("   • 12 color choices")
    print("   • Customizable display name")
    print("\n" + "="*50)
    app.run(host='0.0.0.0', port=5000, debug=True)
