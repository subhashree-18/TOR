# TOR Unveil - Deployment Guide for Tamil Nadu Police

## 🎯 Deployment Objectives

- **High Availability**: Ensure 24/7 investigation tool availability
- **Data Security**: Protect investigation data with encryption
- **Audit Trail**: Maintain forensic compliance records
- **Scalability**: Support multiple concurrent investigators
- **Performance**: Fast query response for 10K+ relays

---

## 📋 Pre-Deployment Checklist

### Infrastructure Requirements

- [ ] Ubuntu 20.04 LTS or later (recommended)
- [ ] 4 CPU cores minimum
- [ ] 8 GB RAM minimum
- [ ] 100 GB SSD storage
- [ ] Docker 20.10+
- [ ] Docker Compose 2.0+
- [ ] Internet connectivity for TOR metadata updates

### Security Preparation

- [ ] Isolated network segment configured
- [ ] Firewall rules drafted
- [ ] SSL certificates obtained (if public-facing)
- [ ] Backup strategy defined
- [ ] Audit logging enabled
- [ ] User authentication method chosen

### Access Control

- [ ] Authorized user list prepared
- [ ] Role definitions documented
- [ ] Chain of custody procedures drafted
- [ ] Investigation logging policy established

---

## 🚀 Step-by-Step Deployment

### Phase 1: Server Setup (30 minutes)

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.16.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

### Phase 2: Application Deployment (15 minutes)

```bash
# Create deployment directory
mkdir -p /opt/tor-unveil-prod
cd /opt/tor-unveil-prod

# Clone repository
sudo git clone <repository-url> .
sudo chown -R $USER:$USER .

# Create production environment file
cp .env.example .env.prod
nano .env.prod

# Required environment variables:
# MONGO_URI=mongodb://torunveil-mongo:27017
# REACT_APP_API_URL=http://localhost:8000
# LOG_LEVEL=INFO
# NODE_ENV=production

# Create docker-compose override for production
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'
services:
  mongo:
    restart: always
    volumes:
      - mongo_data:/data/db
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
  backend:
    restart: always
    environment:
      - MONGO_URI=mongodb://admin:${MONGO_PASSWORD}@mongo:27017
    depends_on:
      - mongo
  frontend:
    restart: always
    environment:
      - REACT_APP_API_URL=${API_URL}

volumes:
  mongo_data:
    driver: local
EOF

# Start services with compose override
docker-compose -f infra/docker-compose.yml -f docker-compose.prod.yml up -d
```

### Phase 3: Configuration (20 minutes)

```bash
# Verify all containers running
docker ps

# Check logs
docker logs torunveil-backend
docker logs torunveil-frontend

# Initialize MongoDB data
docker exec torunveil-backend curl http://localhost:8000/relays/fetch

# Wait for data to load (2-5 minutes)
sleep 300

# Generate initial paths
docker exec torunveil-backend curl http://localhost:8000/paths/generate

# Verify APIs
curl http://localhost:8000/relays?limit=1
curl http://localhost:8000/paths/top?limit=1
```

### Phase 4: Reverse Proxy Setup (nginx + SSL)

```bash
# Install nginx
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Create nginx config
sudo nano /etc/nginx/sites-available/tor-unveil

# Configuration template:
server {
    listen 80;
    server_name investigation.police.tn.gov.in;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name investigation.police.tn.gov.in;
    
    ssl_certificate /etc/letsencrypt/live/investigation.police.tn.gov.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/investigation.police.tn.gov.in/privkey.pem;
    
    # Frontend proxy
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Backend API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/tor-unveil /etc/nginx/sites-enabled/

# Test nginx
sudo nginx -t

# Enable SSL certificate
sudo certbot certonly --nginx -d investigation.police.tn.gov.in

# Reload nginx
sudo systemctl reload nginx
```

---

## 🔒 Security Hardening

### Network Security

```bash
# Configure firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (adjust as needed)
sudo ufw allow 22/tcp

# Allow web traffic
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block MongoDB external access (must be internal only!)
# DO NOT expose port 27017 to internet

# Allow specific internal networks
sudo ufw allow from 10.0.0.0/8 to any port 8000  # Backend API
```

### MongoDB Security

```bash
# Create MongoDB admin user
docker exec torunveil-mongo mongosh << 'EOF'
use admin
db.createUser({
  user: "admin",
  pwd: "SecurePassword123!",
  roles: ["root"]
})
db.createUser({
  user: "tor_unveil_app",
  pwd: "AppPassword456!",
  roles: ["readWrite"]
})
EOF

# Update connection string in environment
MONGO_URI=mongodb://tor_unveil_app:AppPassword456!@mongo:27017/tor_unveil

# Enable MongoDB authentication
docker exec torunveil-mongo mongosh --eval "db.adminCommand('setParameter', {authenticationMechanisms: ['SCRAM-SHA-256']})"
```

### Container Security

```bash
# Run containers with security restrictions
docker run \
  --security-opt=no-new-privileges:true \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  --read-only \
  --tmpfs /tmp \
  ...
```

---

## 🔄 Maintenance Tasks

### Daily
- Monitor container health: `docker ps`
- Check disk space: `df -h`
- Review error logs: `docker logs --tail 100 torunveil-backend`

### Weekly
- Backup MongoDB data
- Review firewall logs
- Check certificate expiration: `certbot certificates`

### Monthly
- Update Docker images: `docker pull`
- Review investigation logs
- Test backup restoration
- Performance optimization

### Quarterly
- Full disaster recovery drill
- Security audit
- Update documentation

### Automation (Crontab)

```bash
# Daily backup
0 2 * * * docker exec torunveil-mongo mongodump --out /backups/$(date +\%Y\%m\%d)

# Weekly MongoDB optimization
0 3 * * 0 docker exec torunveil-mongo db.paths.reIndex()

# Monthly certificate renewal check
0 4 1 * * certbot renew --quiet
```

---

## 📊 Performance Tuning

### MongoDB Optimization

```javascript
// Create indices for fast queries
db.paths.createIndex({score: -1})
db.paths.createIndex({entry_fingerprint: 1})
db.paths.createIndex({exit_country: 1})
db.relays.createIndex({country: 1})
db.relays.createIndex({bandwidth: -1})

// Monitor index usage
db.collection.aggregate([{$indexStats: {}}])

// Analyze query performance
db.collection.find({...}).explain("executionStats")
```

### Container Resources

```yaml
# docker-compose.prod.yml resource limits
mongo:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G

backend:
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 2G

frontend:
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 1G
```

---

## 🆘 Disaster Recovery

### Backup Strategy

```bash
# Full backup
docker exec torunveil-mongo mongodump --archive=/backups/tor-unveil-$(date +%Y%m%d).archive

# Incremental backup (oplog)
mongodump --oplog --out=/backups/incremental-$(date +%Y%m%d)

# Store backups securely
scp /backups/* backup_server:/secure_backup/

# Encrypt backups
gpg --encrypt --recipient police@tn.gov.in /backups/*.archive
```

### Recovery Procedures

```bash
# Step 1: Stop services
docker-compose -f infra/docker-compose.yml down

# Step 2: Restore MongoDB
docker-compose -f infra/docker-compose.yml up -d mongo
docker exec torunveil-mongo mongorestore --archive=/backups/tor-unveil-YYYYMMDD.archive

# Step 3: Restart all services
docker-compose -f infra/docker-compose.yml up -d

# Step 4: Verify data
curl http://localhost:8000/relays?limit=1
```

---

## 📈 Monitoring & Alerts

### Prometheus Metrics (Optional)

```yaml
# Add to docker-compose.prod.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

alertmanager:
  image: prom/alertmanager
  ports:
    - "9093:9093"
```

### Key Metrics to Monitor

- Container CPU usage < 80%
- Container memory usage < 75%
- Disk space > 20% free
- MongoDB query latency < 100ms
- API response time < 500ms
- MongoDB oplog health

---

## 👥 User Management

### Create Authorized User Accounts

```bash
# System user for application
sudo useradd -r -s /bin/false tor-unveil
sudo usermod -aG docker tor-unveil

# SSH users for administrators
sudo useradd -m -s /bin/bash admin1
sudo usermod -aG docker admin1

# Configure sudo permissions
echo "admin1 ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose" | sudo tee -a /etc/sudoers
```

### Access Control Policy

```
Investigation Officer Level 1:
- View Dashboard & Paths
- Export reports

Investigation Officer Level 2:
- All Level 1 permissions
- Manage investigations
- Access Analysis page

System Administrator:
- All permissions
- Container management
- Backups & security
```

---

## 📝 Compliance & Audit

### Investigation Logging

```bash
# Enable Docker logging driver
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "10",
    "labels": "investigation_id,officer_id"
  }
}
EOF

sudo systemctl restart docker
```

### Audit Trail

```bash
# All API calls are logged with:
# - Timestamp
# - User ID
# - Query parameters
# - Result count
# - IP address
# - Response time

# View logs
docker logs torunveil-backend | grep "AUDIT"

# Export for compliance
docker logs torunveil-backend | grep "AUDIT" > audit_trail_$(date +%Y%m%d).log
```

---

## 🎯 Post-Deployment Validation

### Security Checklist

- [ ] Firewall rules active and tested
- [ ] HTTPS working with valid certificate
- [ ] MongoDB requires authentication
- [ ] No ports exposed externally except 80/443
- [ ] SSH key authentication configured
- [ ] Backups tested and restorable
- [ ] Audit logging enabled
- [ ] User accounts created with proper permissions
- [ ] Monitoring configured
- [ ] Disaster recovery plan documented

### Performance Checklist

- [ ] Frontend loads in < 2 seconds
- [ ] API responses < 500ms
- [ ] 1000+ relays load smoothly
- [ ] No memory leaks observed
- [ ] Database indices created
- [ ] Backups complete successfully

### Compliance Checklist

- [ ] Legal disclaimers displayed
- [ ] Audit trail functioning
- [ ] Chain of custody procedures documented
- [ ] Officer training completed
- [ ] Investigation log template prepared
- [ ] Report templates include disclaimers

---

**Document Version**: 1.0
**Last Updated**: December 13, 2025
**Status**: Ready for Production Deployment
