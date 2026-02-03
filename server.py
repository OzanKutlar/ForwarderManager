#!/usr/bin/env python3
"""
SSH Port Forwarding Manager Server
Generates SSH commands and creates temporary users for sharing
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import subprocess
import secrets
import string
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configuration
CONFIG_FILE = 'port_forwards.json'
TEMP_USERS_FILE = 'temp_users.json'


def load_config():
    """Load port forwarding configurations"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return []


def save_config(configs):
    """Save port forwarding configurations"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(configs, f, indent=2)


def load_temp_users():
    """Load temporary users"""
    if os.path.exists(TEMP_USERS_FILE):
        with open(TEMP_USERS_FILE, 'r') as f:
            return json.load(f)
    return []


def save_temp_users(users):
    """Save temporary users"""
    with open(TEMP_USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def generate_password(length=16):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_ssh_command(local_port, remote_host, remote_port, ssh_user, ssh_host, ssh_port=22, reverse=False):
    """Generate SSH port forwarding command"""
    if reverse:
        # Remote port forwarding: -R remote_port:localhost:local_port
        cmd = f"ssh -R {remote_port}:localhost:{local_port} {ssh_user}@{ssh_host}"
    else:
        # Local port forwarding: -L local_port:remote_host:remote_port
        cmd = f"ssh -L {local_port}:{remote_host}:{remote_port} {ssh_user}@{ssh_host}"
    
    if ssh_port != 22:
        cmd += f" -p {ssh_port}"
    
    # Add flags for background and connection keep-alive
    cmd += " -N -f"
    
    return cmd


def create_temp_user(username, password):
    """Create a temporary user with no permissions"""
    try:
        # Create user with no shell and no home directory
        subprocess.run([
            'sudo', 'useradd', 
            '-s', '/bin/false',  # No shell access
            '-M',  # No home directory
            username
        ], check=True, capture_output=True, text=True)
        
        # Set password
        proc = subprocess.Popen(
            ['sudo', 'chpasswd'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        proc.communicate(input=f"{username}:{password}\n")
        
        return True, "User created successfully"
    except subprocess.CalledProcessError as e:
        return False, f"Error creating user: {e.stderr}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def delete_temp_user(username):
    """Delete a temporary user"""
    try:
        subprocess.run(['sudo', 'userdel', username], check=True, capture_output=True, text=True)
        return True, "User deleted successfully"
    except subprocess.CalledProcessError as e:
        return False, f"Error deleting user: {e.stderr}"
    except Exception as e:
        return False, f"Error: {str(e)}"


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/generate-command', methods=['POST'])
def generate_command():
    """Generate SSH port forwarding command"""
    data = request.json
    
    try:
        local_port = int(data.get('localPort'))
        remote_host = data.get('remoteHost', 'localhost')
        remote_port = int(data.get('remotePort'))
        ssh_user = data.get('sshUser')
        ssh_host = data.get('sshHost')
        ssh_port = int(data.get('sshPort', 22))
        reverse = data.get('reverse', False)
        
        command = generate_ssh_command(
            local_port, remote_host, remote_port,
            ssh_user, ssh_host, ssh_port, reverse
        )
        
        # Save configuration
        configs = load_config()
        config = {
            'id': len(configs) + 1,
            'name': data.get('name', f'Port Forward {len(configs) + 1}'),
            'localPort': local_port,
            'remoteHost': remote_host,
            'remotePort': remote_port,
            'sshUser': ssh_user,
            'sshHost': ssh_host,
            'sshPort': ssh_port,
            'reverse': reverse,
            'command': command,
            'created': datetime.now().isoformat()
        }
        configs.append(config)
        save_config(configs)
        
        return jsonify({
            'success': True,
            'command': command,
            'config': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/configs', methods=['GET'])
def get_configs():
    """Get all saved configurations"""
    configs = load_config()
    return jsonify({
        'success': True,
        'configs': configs
    })


@app.route('/api/configs/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    """Delete a configuration"""
    configs = load_config()
    configs = [c for c in configs if c['id'] != config_id]
    save_config(configs)
    return jsonify({
        'success': True
    })


@app.route('/api/create-temp-user', methods=['POST'])
def create_temp_user_endpoint():
    """Create a temporary user for sharing"""
    data = request.json
    
    # Generate username and password
    username = f"temp_{secrets.token_hex(4)}"
    password = generate_password()
    
    # Create the user
    success, message = create_temp_user(username, password)
    
    if success:
        # Save to temp users list
        temp_users = load_temp_users()
        
        # Set expiration (default 24 hours)
        expires_hours = data.get('expiresHours', 24)
        expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat()
        
        user_data = {
            'username': username,
            'password': password,
            'created': datetime.now().isoformat(),
            'expiresAt': expires_at,
            'sshHost': data.get('sshHost', 'your-vps-host'),
            'sshPort': data.get('sshPort', 22)
        }
        
        temp_users.append(user_data)
        save_temp_users(temp_users)
        
        return jsonify({
            'success': True,
            'user': user_data
        })
    else:
        return jsonify({
            'success': False,
            'error': message
        }), 400


@app.route('/api/temp-users', methods=['GET'])
def get_temp_users():
    """Get all temporary users"""
    temp_users = load_temp_users()
    
    # Clean up expired users
    now = datetime.now()
    active_users = []
    
    for user in temp_users:
        expires_at = datetime.fromisoformat(user['expiresAt'])
        if expires_at > now:
            active_users.append(user)
        else:
            # Delete expired user
            delete_temp_user(user['username'])
    
    save_temp_users(active_users)
    
    return jsonify({
        'success': True,
        'users': active_users
    })


@app.route('/api/temp-users/<username>', methods=['DELETE'])
def delete_temp_user_endpoint(username):
    """Delete a temporary user"""
    success, message = delete_temp_user(username)
    
    if success:
        # Remove from list
        temp_users = load_temp_users()
        temp_users = [u for u in temp_users if u['username'] != username]
        save_temp_users(temp_users)
        
        return jsonify({
            'success': True
        })
    else:
        return jsonify({
            'success': False,
            'error': message
        }), 400


if __name__ == '__main__':
    # Create directories if they don't exist
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    print("Starting SSH Port Forwarding Manager...")
    print("Access the web interface at: http://localhost:5000")
    print("\nNote: Creating temporary users requires sudo privileges.")
    print("You may need to configure sudoers to allow the script to run useradd/userdel without password.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
