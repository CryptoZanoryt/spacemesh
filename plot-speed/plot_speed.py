#!/usr/bin/env python3
#
# plot_speed.py
#
# Based on original plot_speed.py, with impropvements.
#
# Author: Zanoryt <zanoryt@protonmail.com>
#

import os
import re
import sys
import json
import datetime
import platform
import subprocess

uname = platform.uname()
operating_system = sys.platform
nvidia = False
amd = False
print_header = True

def detect_gpus():
  try:
    subprocess.check_output('nvidia-smi')
    nvidia = True
  except Exception: # this command not being found can raise quite a few different errors depending on the configuration
    nvidia = False
  try:
    subprocess.check_output('rocm-smi')
    amd = True
  except Exception:
    amd = False

  if nvidia or amd:
    if nvidia:
      print('GPU: Nvidia')
      subprocess.run('nvidia-smi -L')
    if amd:
      print('GPU: AMD')
  else:
    print('GPU: Not found. Maybe we are evaluating files over the network, or not on the PoST gen host.')
  print()

def print_syntax():
  print("syntax: python plot_speed.py <directory>")
  sys.exit(1)

if len(sys.argv) < 2:
  print_syntax()

if print_header:
  print("SpaceMesh PoST Plot Speed (https://github.com/CryptoZanoryt/plot-speed)")
  print()
  print(f"Platform: {uname.system} {uname.release}")
  detect_gpus()

directory = sys.argv[1]
if not os.path.isdir(directory):
    print("The provided directory does not exist.")
    sys.exit(1)

# Read postdata metadata
with open(directory + "/postdata_metadata.json", "r") as file:
    json_data = file.read()
data = json.loads(json_data)
num_units = data['NumUnits']
max_file_size = data['MaxFileSize']
gb_size = 1024**3
total_post_size_GiB = num_units * 64

pattern = r"postdata_(\d+)\.bin"
files = os.listdir(directory)
files = [file for file in files if os.path.isfile(os.path.join(directory, file))]
files = [file for file in os.listdir(directory) if re.match(pattern, file)]

# Calculate current post size
current_post_size_GiB = 0
for file in files:
  file_path = os.path.join(directory, file)
  current_post_size_GiB += os.path.getsize(file_path) / gb_size

# Sort the files by modification time in descending order
files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)

# Sort by size
files_by_size = sorted(files, key=lambda x: os.path.getsize(os.path.join(directory, x)), reverse=True)

first_file = None
first_file_size = 0
total_size = 0
most_recent_complete_file = None
second_most_recent_complete_file = None

# Check if at least two files exist
if len(files) >= 2:
  # Get the most recent file that is complete (equal to the size of max_file_size)
  for file in files_by_size:
    file_path = os.path.join(directory, file)
    if os.path.getsize(file_path) == max_file_size:
      most_recent_complete_file = second_most_recent_complete_file
      second_most_recent_complete_file = os.path.join(directory, file)
      if most_recent_complete_file is not None and second_most_recent_complete_file is not None:
        break

  # Get the size of the first file in the list
  first_file = os.path.join(directory, files[-1])
  almost_last_file = os.path.join(directory, files[1])
  last_file = os.path.join(directory, files[0])

  first_file_size = os.path.getsize(first_file)

  # Get the total size of the files in the directory except the first file in the list
  total_size = 0
  for file in files[:-1]:
    file_path = os.path.join(directory, file)
    total_size += os.path.getsize(file_path)

# Calculate the time difference and throughput if both files are found
if first_file is not None and most_recent_complete_file is not None and last_file is not None:
  first_time = os.path.getmtime(first_file)
  most_recent_time = os.path.getmtime(most_recent_complete_file)
  last_time = os.path.getmtime(last_file)
  first_time_diff = abs(last_time - first_time)
  most_recent_time_diff = abs(last_time - most_recent_time)
  #print(f"complete {most_recent_complete_file} {most_recent_time}")
  #print(f"last {last_file} {last_time}")
  #print(f"total_size {total_size}")
  #print(f"first_file_size {first_file_size}")

  # Calculate throughput in MiB/s
  size_MiB = (total_size - first_file_size) / (1024 * 1024)  # Convert size to MiB
  throughput_MiBps = size_MiB / first_time_diff

  last_size = os.path.getsize(last_file)
  most_recent_complete_file_size = os.path.getsize(most_recent_complete_file)
  recent_size_MiB = (last_size) / (1024 * 1024)
  recent_throughput_MiBps = recent_size_MiB / most_recent_time_diff
  #print(f"size_MiB {size_MiB}")
  #print(f"throughput_MiBps {throughput_MiBps}")
  #print(f"recent_size_MiB {recent_size_MiB}")
  #print(f"recent_throughput_MiBps {recent_throughput_MiBps}")

  # Calculate time difference in minutes and seconds
  first_minutes, first_seconds = divmod(first_time_diff, 60)
  first_minutes = int(first_minutes)  # Convert minutes to integer
  first_seconds = int(first_seconds)  # Convert seconds to integer
  first_time_delta_string = f"{first_minutes:02d}m {first_seconds:02d}s"

  most_recent_minutes, most_recent_seconds = divmod(most_recent_time_diff, 60)
  most_recent_minutes = int(most_recent_minutes)  # Convert minutes to integer
  most_recent_seconds = int(most_recent_seconds)  # Convert seconds to integer
  most_recent_time_delta_string = f"{most_recent_minutes:02d}m {most_recent_seconds:02d}s"

  progress_percent = current_post_size_GiB / total_post_size_GiB * 100

  # estimated time to finish
  remaining_post_size_GiB = total_post_size_GiB - current_post_size_GiB
  etf_sec = remaining_post_size_GiB / (throughput_MiBps / 1024)
  days, remainder = divmod(etf_sec, 86400)    # 86400 seconds in a day
  hours, remainder = divmod(remainder, 3600)  # 3600 seconds in an hour
  minutes, seconds = divmod(remainder, 60)
  days = int(days)
  hours = int(hours)
  minutes = int(minutes)
  seconds = int(seconds)
  etf_string = f"{days:02d}d {hours:02d}h {minutes:02d}m {seconds:02d}s"

  recent_etf_sec = remaining_post_size_GiB / (recent_throughput_MiBps / 1024)
  recent_days, recent_remainder = divmod(recent_etf_sec, 86400)    # 86400 seconds in a day
  recent_hours, recent_remainder = divmod(recent_remainder, 3600)  # 3600 seconds in an hour
  recent_minutes, recent_seconds = divmod(recent_remainder, 60)
  recent_days = int(recent_days)
  recent_hours = int(recent_hours)
  recent_minutes = int(recent_minutes)
  recent_seconds = int(recent_seconds)
  recent_etf_string = f"{recent_days:02d}d {recent_hours:02d}h {recent_minutes:02d}m {recent_seconds:02d}s"

  # estimated finish date
  current_date = datetime.datetime.now()
  time_diff_timedelta = datetime.timedelta(seconds=etf_sec)
  recent_time_diff_timedelta = datetime.timedelta(seconds=recent_etf_sec)
  efd = current_date + recent_time_diff_timedelta
  efd = efd.strftime("%Y-%m-%d %H:%M")

  print(f"Progress .................................... {current_post_size_GiB:.2f} of {total_post_size_GiB:.2f} GiB ({progress_percent:.2f}%)")
  print(f"PoST Size ................................... All: {total_post_size_GiB} GiB, Current: {current_post_size_GiB} GiB, Remain: {remaining_post_size_GiB} GiB")
  print(f"First complete file ......................... {first_file}")
  print(f"Previous complete file ...................... {second_most_recent_complete_file}")
  print(f"Most recently complete file ................. {most_recent_complete_file}")
  print(f"Current file ................................ {last_file}")
  print(f"Time since last completed file .............. {most_recent_time_delta_string}")
  print(f"Recent Plotting speed ....................... {recent_throughput_MiBps:.2f} MiB/s")
  print(f"Average Plotting speed ...................... {throughput_MiBps:.2f} MiB/s")
  print(f"Estimated finish time ....................... {recent_etf_string}")
  print(f"Estimated finish date ....................... {efd}")
else:
  print("There are not enough files in the directory yet. Will calculate once the first two files complete.")
