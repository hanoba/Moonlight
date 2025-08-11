sudo cp amserver.service /etc/systemd/system/
sudo systemctl daemon-reload      # oder "daemon-reexec", wenn completter Neustart von systemd erforderlich ist
sudo systemctl enable amserver
sudo systemctl start amserver

