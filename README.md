# An0m0s VPN Manager

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey)

**Enterprise-grade OpenVPN controller with killswitch firewall protection**

</div>

## 📋 Overview

An0m0s VPN Manager is a modern, secure GUI application for managing OpenVPN connections on Linux systems. Built with Python and Tkinter, it features a premium dark theme interface, network killswitch protection, and real-time connection monitoring.

## ✨ Features

- **🎨 Premium Dark UI** - Modern, responsive interface with smooth animations
- **🔒 Network Killswitch** - Blocks all traffic outside VPN tunnel using iptables
- **🌍 IP & Location Detection** - Real-time public IP and geolocation tracking
- **⚡ Easy Configuration** - Simple .ovpn file upload and management
- **🛡️ Security First** - Root privilege management with pkexec
- **📊 Connection Monitoring** - Real-time VPN status and process tracking
- **🔄 Automatic Recovery** - Network restoration and cleanup tools
- **📱 Responsive Design** - Adapts to different screen sizes (1-column/2-column layout)

## 🖼️ Screenshots

<div align="center">
  <img src="images/screenshot-main.png?raw=true" alt="An0m0s VPN Manager Interface" width="800">
  <p><em>An0m0s VPN Manager - Premium Dark Theme Interface</em></p>
</div>

### Key Interface Features:
- **Connection Dashboard** - Real-time IP address and location tracking
- **OpenVPN Profile Manager** - Easy .ovpn file configuration
- **Killswitch Toggle** - Visual security control with one-click activation
- **Control Panel** - Start VPN, Force Stop, Status Check, and Network Restore
- **Responsive Design** - Clean, modern dark theme optimized for all screen sizes

## 📦 Requirements

### System Requirements
- **OS**: Linux (tested on Debian/Ubuntu/Kali)
- **Python**: 3.8 or higher
- **OpenVPN**: Must be installed
- **Root Access**: Required for VPN and firewall management

### Python Dependencies
- `tkinter` (usually pre-installed with Python)
- `requests` - For IP geolocation API calls

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Anasx1111/An0m0s-VPN.git
cd An0m0s-VPN
```

### 2. Install System Dependencies
```bash
# Ubuntu/Debian/Kali
sudo apt update
sudo apt install python3 python3-tk openvpn iptables
```

### 3. Install Python Dependencies
```bash
# Create virtual environment (recommended)
python3 -m venv env
source env/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 4. Make the Script Executable
```bash
chmod +x An0m0s_vpn.py
```

## 🎯 Usage

### Running the Application

The application requires root privileges to manage VPN connections and firewall rules:

```bash
# Run with pkexec (recommended - GUI authentication)
pkexec python3 An0m0s_vpn.py

# Or with sudo
sudo python3 An0m0s_vpn.py
```

### Quick Start Guide

1. **Launch the application** with root privileges
2. **Load .ovpn file** - Click "Load .ovpn file" and select your OpenVPN configuration
3. **Enable Killswitch** (optional) - Toggle the killswitch to block all non-VPN traffic
4. **Start VPN** - Click "Start VPN" to establish connection
5. **Monitor Status** - View your connection status, IP, and location in real-time

### Killswitch Feature

The killswitch uses iptables to block all internet traffic except:
- VPN tunnel (tun/tap interfaces)
- VPN server connections
- Localhost traffic
- DNS and DHCP (before VPN connects)

**⚠️ Warning**: When killswitch is active and VPN disconnects, you will have no internet access until you disable the killswitch or reconnect.

### Getting OpenVPN Configuration Files

If you need a .ovpn configuration file, you can:
- Use the built-in link to download free configs
- Get configs from your VPN provider
- Create your own OpenVPN server configuration

## 🎮 Controls

| Button | Description |
|--------|-------------|
| **Load .ovpn file** | Upload OpenVPN configuration |
| **Start VPN** | Initiate VPN connection |
| **Force Stop** | Immediately terminate VPN process |
| **Status Check** | Verify VPN connection status |
| **Restore Network** | Remove all firewall rules |
| **Refresh** | Update IP and location info |
| **Killswitch Toggle** | Enable/disable traffic blocking |

## 🛠️ Technical Details

### Architecture
- **GUI Framework**: Tkinter with custom styling
- **VPN Management**: OpenVPN subprocess control
- **Firewall**: iptables for killswitch implementation
- **Networking**: Requests library for IP geolocation
- **Privilege Elevation**: pkexec for secure root access

### File Structure
```
An0m0s-VPN/
├── An0m0s_vpn.py      # Main application
├── requirements.txt    # Python dependencies
├── README.md          # Documentation
├── LICENSE            # MIT License
└── .gitignore         # Git ignore rules
```

### Security Considerations

1. **Root Privileges**: Application requires root for VPN/firewall management
2. **Killswitch Safety**: Automatically backs up iptables rules before modification
3. **Process Isolation**: VPN runs in separate subprocess
4. **Secure Cleanup**: Proper cleanup on application exit
5. **No Credentials Storage**: Never stores VPN credentials

## 🐛 Troubleshooting

### "App must run with root privileges"
- Use `pkexec` or `sudo` to run the application

### "OpenVPN not found"
```bash
sudo apt install openvpn
```

### "Failed to enable killswitch"
- Ensure `iptables` is installed
- Check if you have root privileges
- Verify no conflicting firewall rules

### VPN won't connect
- Verify .ovpn file is valid
- Check OpenVPN logs: `sudo journalctl -u openvpn`
- Ensure VPN server is reachable

### Internet blocked after closing app
- Reopen app and click "Restore Network"
- Or manually: `sudo iptables -F && sudo iptables -P INPUT ACCEPT && sudo iptables -P OUTPUT ACCEPT`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Anas Gharaibeh**

- GitHub: [@Anasx1111](https://github.com/Anasx1111)
- LinkedIn: [Anas Gharaibeh](https://www.linkedin.com/in/anas-gharaibeh-9746b72b7/)
- Instagram: [@anas.gharibeh](https://www.instagram.com/anas.gharibeh/)

## 🙏 Acknowledgments

- OpenVPN community for the excellent VPN software
- Free VPN config providers
- Python Tkinter community

## ⚠️ Disclaimer

This tool is provided for educational and legitimate use only. Users are responsible for:
- Complying with their VPN provider's terms of service
- Following local laws and regulations
- Using VPN services responsibly

The author is not responsible for misuse of this software.

## 🔮 Future Enhancements

- [ ] Multi-VPN profile management
- [ ] Connection logs and history
- [ ] Auto-reconnect on disconnect
- [ ] Split tunneling support
- [ ] DNS leak protection
- [ ] Custom firewall rules
- [ ] System tray integration
- [ ] Dark/light theme toggle

---

<div align="center">

**⭐ If you find this project useful, please consider giving it a star!**

Made with ❤️ by An0m0s

</div>
