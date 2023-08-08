#!/usr/bin/env python3
#
# This script is used to engage the second stage of the PoST installation onto a remote server.
#
# Usage:
#   stage2.sh <path to config file>
#

import json
import os
from time import sleep
import runpod
import sys

# 1. Load the config details
stage1_path = "/tmp/stage1"
stage2_path = "/tmp/stage2"
os.makedirs(stage2_path, exist_ok=True)
config = json.load(open(f"{stage1_path}/stage1.json"))
# print(config)
print(f"Loaded config from {stage1_path}/stage1.json")
print(f"Node ID: {config['node_id']}")

# 2. Look for runpod availability
runpod.api_key = "YOURKEY"
gpus = runpod.get_gpus()
print("Available GPUs:")
for gpu in gpus:
  print(f"  - {gpu['id']}")
print()

quantity = 4
gpu_selected = { 'id': "NVIDIA GeForce RTX 4090", 'quantity': quantity }
gpu_selected = { 'id': "NVIDIA RTX 6000 Ada Generation", 'quantity': quantity }
disk_size=256
lowest_price = None
ondemand_price = None

while lowest_price is None:
  gpu = runpod.get_gpu(gpu_selected['id'])
  lowest_price = gpu['lowestPrice']['minimumBidPrice']
  ondemand_price = gpu['lowestPrice']['uninterruptablePrice']
  print(gpu)
  sleep(5)

# 3. If runpod is available, run the pod
pod = None
print(f"Trying to run a pod with {quantity} x GPU {gpu_selected['id']} and {disk_size}GB storage...")
print(f"  - Lowest price: {lowest_price * quantity}/hr")
print(f"  - On-demand price: {ondemand_price * quantity}/hr")
print()

# 4. If runpod is not available, wait until it is
print("Waiting for availability...", end='', flush=True)
while pod is None:
  pod = runpod.create_pod(
    name="post test",
    image_name="ghcr.io/smeshcloud/nvidia-cuda-opencl",
    gpu_type_id=gpu_selected['id'],
    gpu_count=gpu_selected['quantity'],
    container_disk_in_gb=disk_size,
    docker_args="bash -c 'wget -O- https://raw.githubusercontent.com/CryptoZanoryt/spacemesh/main/generate-post/generate-post.sh | bash -s ${disk_size} ${config['node_id']}'",
  )
  # print("Pod is not available yet, trying again in 15 seconds...")
  print('.', end='', flush=True)
  sleep(15)
print(' running!')
print()
# print(pod)

print(f"Pod {pod['id']} is now running")
print(f"  - Pod id: {pod['id']}")
print(f"  - SSH command: ssh {pod['machine']['podHostId']}@ssh.runpod.io -i ~/.ssh/id_ed25519")
print()

# 5. Write the pod details to a file
pod_details = {
  'pod_id': pod['id'],
  'pod_host_id': pod['machine']['podHostId'],
  'gpu': {
    'quantity': quantity,
    'type': gpu_selected['id'],
    'lowest_price': lowest_price,
    'ondemand_price': ondemand_price,
  },
  'disk_size': disk_size,
}
json.dump(pod_details, open(f"{stage2_path}/stage2.json", "w"))
print(f"Pod details written to {stage2_path}/stage2.json")
print()

# 5. Wait for the pod to complete
print("Waiting for pod to complete", end='', flush=True)


# 6. If the pod fails, exit with an error
print("Pod failed, exiting with error")

# 7. If the pod succeeds, transfer the PoST files from the pod to a storage platform (Backblaze B2)
print("Pod run completed, transferring PoST files to storage platform")
