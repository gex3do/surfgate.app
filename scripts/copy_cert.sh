# sudo certbot -d go.surfgate.app --manual --preferred-challenges dns certonly

sudo cp /etc/letsencrypt/archive/go.surfgate.app/fullchain8.pem /home/dim/Projects/surfgate.app/src/keys/production/cert.pem
sudo cp /etc/letsencrypt/archive/go.surfgate.app/privkey8.pem /home/dim/Projects/surfgate.app/src/keys/production/private.pem

sudo chown dim:dim /home/dim/Projects/surfgate.app/src/keys/production/cert.pem
sudo chown dim:dim /home/dim/Projects/surfgate.app/src/keys/production/private.pem

sudo chmod 775 /home/dim/Projects/surfgate.app/src/keys/production/cert.pem
sudo chmod 775 /home/dim/Projects/surfgate.app/src/keys/production/private.pem

