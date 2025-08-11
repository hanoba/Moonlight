sudo cp amserver.service /etc/systemd/system/
sudo systemctl daemon-reexec      # oder daemon-reload bei Änderung
sudo systemctl enable meinservice
sudo systemctl start meinservice

