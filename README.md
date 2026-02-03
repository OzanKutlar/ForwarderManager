# SSH Port Forwarding Manager

A sleek, modern web application for managing SSH port forwarding commands and creating temporary users for sharing access with friends.

## Features

- **Command Generator**: Never remember complex SSH port forwarding syntax again
- **Auto-Detection**: SSH host is automatically detected from the URL you're accessing
- **Configuration Management**: Save and manage multiple port forwarding configurations
- **Temporary User Creation**: Create restricted users with no permissions for sharing
- **Modern UI**: Sleek interface with smooth animations and cyberpunk-inspired design
- **Auto-expiration**: Temporary users automatically expire after a set time
- **Cross-browser Copy**: Clipboard copying works in all modern browsers

## Prerequisites

- Python 3.8 or higher
- sudo privileges (for creating temporary users)
- A VPS or server where you want to manage SSH port forwarding

## Installation

1. Clone or download this project to your server

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Configure sudoers to allow temporary user creation (optional but recommended):
```bash
sudo visudo
```

Add the following line (replace `your_username` with your actual username):
```
your_username ALL=(ALL) NOPASSWD: /usr/sbin/useradd, /usr/sbin/userdel, /usr/bin/chpasswd
```

This allows the script to create and delete users without requiring a password prompt.

## Usage

### Starting the Server

```bash
python3 server.py
```

The server will start on `http://localhost:5000`. Access the web interface by navigating to this URL in your browser.

### Generating SSH Commands

1. Fill in the form with your port forwarding details:
   - **Configuration Name**: A friendly name for this setup
   - **Local Port**: The port on your local machine
   - **Remote Port**: The port on the remote server
   - **Remote Host**: Usually "localhost" for standard forwarding
   - **SSH User**: Your username on the VPS
   - **SSH Host**: Auto-detected from the URL (e.g., if accessing via `http://82.118.227.31:5000`, the SSH host will be `82.118.227.31`)
   - **SSH Port**: SSH port (default: 22)
   - **Reverse Port Forwarding**: Check this for reverse tunnels

2. Click "Generate SSH Command"

3. Copy the generated command and run it in your terminal

### Creating Temporary Users

1. Navigate to the "Share with Friends" section

2. Fill in:
   - **VPS Host**: Your server hostname
   - **SSH Port**: SSH port (default: 22)
   - **Expires In**: Hours until the user expires (default: 24)

3. Click "Create Temporary User"

4. Share the generated credentials with your friend

**Important**: Temporary users are created with `/bin/false` as their shell, preventing them from logging in directly. They can only use SSH for port forwarding.

## SSH Port Forwarding Basics

### Local Port Forwarding
Forward a local port to a remote server:
```bash
ssh -L 8080:localhost:80 user@server
```
This makes `localhost:8080` on your machine connect to `localhost:80` on the server.

### Reverse Port Forwarding
Expose a local port to a remote server:
```bash
ssh -R 8080:localhost:3000 user@server
```
This makes port 8080 on the server forward to `localhost:3000` on your machine.

### Command Flags
- `-N`: Don't execute remote commands (for port forwarding only)
- `-f`: Run in background
- `-p PORT`: Specify SSH port

## Security Considerations

1. **Temporary Users**: Created users have no shell access and minimal permissions
2. **Auto-Expiration**: Users are automatically deleted when they expire
3. **Random Passwords**: Strong random passwords are generated automatically
4. **Firewall**: Ensure your VPS firewall only allows necessary ports
5. **SSH Keys**: Consider using SSH key authentication instead of passwords

## File Structure

```
.
├── server.py              # Flask backend server
├── templates/
│   └── index.html         # Web interface
├── static/                # Static files (auto-created)
├── requirements.txt       # Python dependencies
├── port_forwards.json     # Saved configurations
└── temp_users.json        # Temporary user data
```

## Troubleshooting

### Permission Errors
If you get permission errors when creating users, ensure you've configured sudoers correctly or run the script with sudo:
```bash
sudo python3 server.py
```

### Port Already in Use
If port 5000 is already in use, modify the last line in `server.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8000)  # Change port number
```

### SSH Connection Issues
- Verify your VPS allows SSH connections
- Check firewall rules on both local and remote machines
- Ensure SSH service is running: `sudo systemctl status ssh`

## API Endpoints

- `POST /api/generate-command` - Generate SSH command
- `GET /api/configs` - Get all configurations
- `DELETE /api/configs/<id>` - Delete a configuration
- `POST /api/create-temp-user` - Create temporary user
- `GET /api/temp-users` - Get all active temporary users
- `DELETE /api/temp-users/<username>` - Delete a temporary user

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## Acknowledgments

- Built with Flask and modern web technologies
- Designed with a focus on user experience and security