# ApexMotors One-Liner Setup

Install and run the **ApexMotors application** with a single command.  

The script will:

- Install Git, Docker, Docker Compose, OpenSSL  
- Create system user `appuser`  
- Clone repository into `/opt/apexmotors`  
- Prompt for `.env` PostgreSQL credentials (with defaults)  
- Generate self-signed SSL certificates in `/etc/ssl/apexmotors`  
- Set up Docker Compose as a systemd service (`docker-compose-app`)  
- Import `db.sql` automatically from the repository root  
- Configure Nginx to serve the app over HTTPS  

---

## One-Liner Installation

Run the following command as root:

```bash
sudo bash -c "$(curl -sSL https://raw.githubusercontent.com/ramazan-qandaxov/apexmotors/main/install.sh)"
