#!/bin/bash
#
# This script generates the post files for the specified node.
#
## Usage:
#
#   ./generate_post.sh
#
## Author:
#
# Zanoryt <zanoryt@protonmail.com>
#

PLOT_SPEED_URL="https://github.com/CryptoZanoryt/spacemesh/blob/main/plot-speed/smesher-plot-speed.py"
POSTCLI_VERSION="0.8.11"
POSTCLI_PATH="/tmp/postcli"
POSTCLI_FULLPATH="${POSTCLI_PATH}/postcli"
PLOT_SPEED_FULLPATH="${POSTCLI_PATH}/smesher-plot-speed.py"
POST_DATA_PATH="/tmp/post-data"

# Update system and install dependencies
apt update
apt install -y clinfo
apt install -y nvtop htop screen unzip xxd

# Download postcli
rm -rf $POSTCLI_PATH
mkdir -p $POSTCLI_PATH
wget -O- https://github.com/spacemeshos/post/releases/download/v${POSTCLI_VERSION}/postcli-Linux.zip | unzip -u - -d $POSTCLI_PATH
chmod +x $POSTCLI_FULLPATH

wget -O $PLOT_SPEED_FULL_PATH $PLOT_SPEED_URL

# nodeId in base64 format
nodeId="URZgMjtU06WgahvNHpvtr89NnB2IIhw2Yo8ZqfZx0ts="
# nodeId in HEX format
id=$(echo "$nodeId" | base64 -d | xxd -p -c 32 -g 32)
echo "ID: ${id}"

labelsPerUnit="4294967296" # 2^32
maxFileSize="2147483648"   # 2^31
# Number of 64 GiB units
numUnits="19"

# 2 or 4
numGpus=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
# convert to int
numGpus=$(($numGpus + 0))
echo "Number of GPUs: ${numGpus}"
commitmentAtxId="9eebff023abb17ccb775c602daade8ed708f0a50d3149a42801184f5b74f2865"
echo "commitmentAtxId: ${commitmentAtxId}"

rm -rf $POST_DATA_PATH
mkdir -p $POST_DATA_PATH

echo "Initializing screen"
screen -d -m -S post
screen -S post -X exec watch -n 5 python3 $PLOT_SPEED_FULLPATH ${POST_DATA_PATH}/
screen -s post -X screen -t nvtop
screen -S post -p nvtop -X exec nvtop
screen -S post -X screen -t htop
screen -S post -p htop -X exec htop

echo "Generating post files..."
for ((i=1; i<=$numGpus; i++))
do
  provider=$((i-1))
  screen -S post -X screen -t post$provider
  screen -S post -p post0 -X exec bash -c "$POSTCLI_FULLPATH -provider $provider -commitmentAtxId $commitmentAtxId -id $id -labelsPerUnit $labelsPerUnit -maxFileSize $maxFileSize -numUnits $numUnits -datadir $POST_DATA_PATH -fromFile $((numUnits*32/numGpus*$provider)) -toFile $((-1+numUnits*32/numGpus*$i)); exec bash"
done

echo "Started generating the PoST data files."
echo ""
echo "To attach to the screen session, run:"
echo ""
echo "  screen -d -r post"
echo ""
echo "Have fun!"

# Sleep forever since things are running in the background
sleep infinity
