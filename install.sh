#!/bin/bash
set -e

if [ $# -eq 0 ]; then
	echo "Must supply a target! Usage:"
	echo "$ sh install.sh <target>"
	exit 1
fi

TARGET="$1"

# Tarball the resources

poetry export --output requirements.txt
tar -czf build/fume-hood.tgz fume-hood.service requirements.txt fume_hood/__init__.py

scp build/fume-hood.tgz "$TARGET"

ssh "$TARGET" << 'EOF'
tar -xzf fume-hood.tgz
rm -f fume-hood.tgz
sudo pip3 install -r requirements.txt
sudo mv fume_hood/__init__.py /usr/local/bin/fume-hood
sudo chown root:root fume-hood.service
sudo chown root:root /usr/local/bin/fume-hood
sudo chmod +x /usr/local/bin/fume-hood
sudo mv fume-hood.service /lib/systemd/system/
sudo systemctl enable fume-hood
sudo systemctl restart fume-hood
rm -rf requirements.txt fume_hood/
EOF
