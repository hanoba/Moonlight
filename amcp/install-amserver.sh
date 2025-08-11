sudo cp amserver.service /etc/systemd/system/
sudo systemctl daemon-reexec      # oder daemon-reload bei Änderung
sudo systemctl enable amserver
sudo systemctl start amserver

