#!/usr/bin/env python3
#
# smesher-plot-speed.py
#
# Based on original plot_speed.py, with impropvements.
#
# Author: Zanoryt <zanoryt@protonmail.com>
#

import base64
import hashlib
import os
import re
import sys
import json
import datetime
import platform
import urllib.request
import subprocess

version = "1.0.0"
uname = platform.uname()
operating_system = None
cpu = { 'name': '' }
gpus = []
provider = 'CPU'
nvidia = False
amd = False
force_cpu = False
force_gpu = False
print_header = True
output_json = False
directory = None
send_report = False
github_url = "https://github.com/CryptoZanoryt/spacemesh/tree/main/plot-speed"


def calculate_current_post_size_GiB(directory):
  current_post_size_GiB = 0
  for file in files:
    file_path = os.path.join(directory, file)
    current_post_size_GiB += os.path.getsize(file_path) / postdata['gb_size']
  return current_post_size_GiB

def detect_cpu():
  global cpu
  if platform.system() == "Windows":
    cpu = {
      'name': platform.processor(),
      'type': platform.processor()
    }
  elif platform.system() == "Darwin":
    os.environ['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/sbin'
    command = ["sysctl", "-n", "machdep.cpu.brand_string"]
    output = subprocess.check_output(command).decode().strip()
    cpu = {
      'name': output,
      'type': output
    }
  elif platform.system() == "Linux":
    command = "cat /proc/cpuinfo"
    all_info = subprocess.check_output(command, shell=True).decode().strip()
    for line in all_info.split("\n"):
      if "model name" in line:
        cpu = {
          'name': re.sub( ".*model name.*:", "", line, 1),
          'type': re.sub( ".*model name.*:", "", line, 1)
        }

def detect_gpus():
  global gpus
  global nvidia
  global amd
  global devices

  if operating_system['system'] == 'Windows':
    command = 'wmic path win32_VideoController get name'
    output = subprocess.check_output(command, shell=True).decode().strip()
    devices = output.split('\r\n')[1:]
    for i in range(len(devices)):
      devices[i] = devices[i].strip()
    if 'NVIDIA' in devices[0]:
      nvidia = True
    if 'AMD' in devices[0]:
      amd = True
    print(devices)
    gpu_list = []
    for device in devices:
      name = device.strip()
      vendor = name.split(None, 1)[0]
      model = name.split(None, 1)[1]
      gpu_list.append({
        'vendor': vendor,
        'model': model,
        'name': name
      })
  elif operating_system['system'] == 'Linux':
    command = 'lspci -vnn | grep VGA'
    output = subprocess.check_output(command, shell=True).decode().strip()
    devices = output.split('\n')
    for i in range(len(devices)):
      devices[i] = devices[i].strip()
    if 'NVIDIA' in devices[0]:
      nvidia = True
    if 'AMD' in devices[0]:
      amd = True
  elif operating_system['system'] == 'macOS':
    command = ['/usr/sbin/system_profiler', 'SPDisplaysDataType']
    output = subprocess.run(command, capture_output=True, text=True).stdout
    gpu_vendor = None
    gpu_model = None

    match = re.search(r'Vendor:\s*(.*) \(.*\)', output)
    if match:
      gpu_vendor = match.group(1)
      print(gpu_vendor)
      if gpu_vendor:
        if 'NVIDIA' in gpu_vendor:
          nvidia = True
        if 'AMD' in gpu_vendor:
          amd = True

    match = re.search(r'Chipset Model:\s*(.*)', output)
    if match:
      gpu_model = match.group(1)
      print(gpu_model)
      if gpu_model:
        if 'NVIDIA' in gpu_model:
          nvidia = True
        if 'AMD' in gpu_model:
          amd = True

    gpus.append({
      'vendor': gpu_vendor,
      'model': gpu_model,
      'name': f"{gpu_vendor} {gpu_model}"
    })

  else:
    print('Unsupported operating system')

  # try:
  #   subprocess.check_output('nvidia-smi')
  #   nvidia = True
  # except Exception: # this command not being found can raise quite a few different errors depending on the configuration
  #   nvidia = False
  # try:
  #   subprocess.check_output('rocm-smi')
  #   amd = True
  # except Exception:
  #   amd = False

def detect_os():
  global operating_system, operating_system_version
  if platform.system() == 'Linux' and hasattr(platform, 'linux_distribution'):
    operating_system = {
      'system': platform.system(),
      'distribution': platform.linux_distribution()[0],
      'version': platform.linux_distribution()[1]
    }
  if platform.system() == 'Darwin' and hasattr(platform, 'mac_ver'):
    operating_system = {
      'system': 'macOS',
      'version': platform.mac_ver()[0]
    }
  if platform.system() == 'Windows' and hasattr(platform, 'win32_ver'):
    operating_system = {
      'system': 'Windows',
      'release': platform.win32_ver()[0],
      'version': platform.win32_ver()[1],
      'service_pack': platform.win32_ver()[2],
      'processor_support': platform.win32_ver()[3],
      'edition': platform.win32_edition()
    }

def detect_provider():
  global provider
  if force_cpu or force_gpu:
    if force_cpu:
      provider = 'CPU'
    if force_gpu:
      provider = 'GPU'
  else:
    if nvidia or amd:
      provider = 'GPU'
    else:
      provider = 'CPU'

def print_cpu_info():
  print('Detected CPU: ' + cpu['type'])

def print_gpu_info():
  if gpus:
    print(f"Detected GPU(s): { ', '.join([gpu['name'] for gpu in gpus]) }")
  elif nvidia or amd:
    if nvidia:
      print('Detected GPU: Nvidia')
      subprocess.run('nvidia-smi -L')
    if amd:
      print('Detected GPU: AMD')
  else:
    print('Detected GPU: N/A')

def print_os_info():
  print(f"Operating System: {operating_system['system']} {operating_system['version']}")

def print_provider_info():
  if force_cpu or force_gpu:
    print(f"Provider: {provider} (forced)")
  else:
    print(f"Provider: {provider}")

def parse_arguments():
  global output_json
  global send_report
  global print_header
  global directory

  if "--json" in sys.argv:
    output_json = True
    print_header = False
    sys.argv.remove("--json")
  if "--no-header" in sys.argv:
    print_header = False
    sys.argv.remove("--no-header")
  if "--report" in sys.argv:
    send_report = True
    sys.argv.remove("--report")
  if "--report-force-cpu" in sys.argv:
    force_cpu = True
    sys.argv.remove("--report-force-cpu")
  if "--report-force-gpu" in sys.argv:
    force_gpu = True
    sys.argv.remove("--report-force-gpu")
  if "--version" in sys.argv:
    print(f"smesher-plot-speed.py version {version}")
    sys.exit(0)
  if "--help" in sys.argv:
    print_syntax()
    sys.exit(0)
  if len(sys.argv) < 2:
    print_syntax()
    sys.exit(1)
  directory = sys.argv[1]
  if not os.path.isdir(directory):
    print("The provided directory does not exist.")
    sys.exit(1)
  if not os.path.isfile(directory + "/postdata_metadata.json"):
    print("The provided directory does not contain postdata_metadata.json.")
    sys.exit(1)
  if not os.path.isfile(directory + "/smeshing_metadata.json"):
    print("The provided directory does not contain smeshing_metadata.json, has the smesher started yet?")
    sys.exit(1)
  if not os.path.isfile(directory + "/postdata_0.bin"):
    print("The provided directory does not contain postdata_0.bin yet.")
    sys.exit(1)
  if not os.path.isfile(directory + "/postdata_1.bin"):
    print("The provided directory does not contain postdata_1.bin yet.")
    sys.exit(1)

def postdata_metadata():
  with open(directory + "/postdata_metadata.json", "r") as file:
      json_data = file.read()
  data = json.loads(json_data)
  node_id = base64.b64decode(data['NodeId']).hex()
  node_md5 = hashlib.md5(node_id.encode()).hexdigest()  # We do this for privacy reasons!
  return {
    'node_md5': node_md5,
    'num_units': data['NumUnits'],
    'max_file_size': data['MaxFileSize'],
    'gb_size': 1024**3,
    'total_post_size_GiB': data['NumUnits'] * 64
  }

def postdata_bin_files(directory):
  pattern = r"postdata_(\d+)\.bin"
  files = os.listdir(directory)
  files = [file for file in files if os.path.isfile(os.path.join(directory, file))]
  files = [file for file in os.listdir(directory) if re.match(pattern, file)]
  return files

def print_output():
  gpu_list = [
    {
      "name": name,
      "count": sum(1 for gpu in gpus if gpu.get("name") == name),
      "vendor": gpu.get("vendor"),
      "model": gpu.get("model")
    }
    for name in set(gpu.get("name") for gpu in gpus)
    for gpu in gpus
    if gpu.get("name") == name
  ]
  data = {
    'app': {
      'name': 'smesher-plot-speed',
      'version': version
    },
    'uname': {
      'machine': uname.machine,
      'processor': uname.processor,
      'system': uname.system,
      'release': uname.release
    },
    'cpu': cpu,
    'gpu': {
      'nvidia': nvidia,
      'amd': amd,
      'devices': gpus,
      'devices_compressed': gpu_list
    },
    'os': operating_system,
    'provider': {
      'force_cpu': force_cpu,
      'force_gpu': force_gpu,
      'type': provider
    },
    'metadata': {
      'postdata': postdata,
      'smeshing': smeshing
    },
    'progress': {
      'progress_percent': progress_percent,
      'current_post_size_GiB': current_post_size_GiB,
      'remaining_post_size_GiB': remaining_post_size_GiB,
      'recent_throughput_MiBps': recent_throughput_MiBps,
      'throughput_MiBps': throughput_MiBps,
      'recent_etf_string': recent_etf_string,
      'efd': efd
    },
    'files': {
      'first': { 'path': first_file, 'size': first_file_size, 'time_since_modified': time_since_first },
      'previous_most_recent_complete': { 'path': previous_most_recent_complete_file, 'size': os.path.getsize(previous_most_recent_complete_file), 'time_since_modified': time_since_previous_most_recent },
      'most_recent_complete': { 'path': most_recent_complete_file, 'size': most_recent_complete_file_size, 'time_since_modified': time_since_most_recent },
      'current': { 'path': current_file, 'size': current_size, 'time_since_modified': time_since_current }
    },
    'most_recent_time_delta_string': most_recent_time_delta_string,
  }

  if send_report:
    data = post_report(data)

  if output_json:
    print(json.dumps(data))
    sys.exit(0)

  print(f"Progress .................................... {current_post_size_GiB:.2f} of {postdata['total_post_size_GiB']:.2f} GiB ({progress_percent:.2f}%)")
  print(f"PoST Size ................................... All: {postdata['total_post_size_GiB']} GiB, Current: {current_post_size_GiB} GiB, Remain: {remaining_post_size_GiB} GiB")
  print(f"First complete file ......................... {first_file}")
  print(f"Previous complete file ...................... {previous_most_recent_complete_file}")
  print(f"Most recently complete file ................. {most_recent_complete_file}")
  print(f"Current file ................................ {current_file}")
  print(f"Time since last completed file .............. {most_recent_time_delta_string}")
  print(f"Recent Plotting speed ....................... {recent_throughput_MiBps:.2f} MiB/s")
  print(f"Average Plotting speed ...................... {throughput_MiBps:.2f} MiB/s")
  print(f"Estimated finish time ....................... {recent_etf_string}")
  print(f"Estimated finish date ....................... {efd}")
  if send_report:
    print(f"Report sent ................................. {data['report']['sent']}")

def print_syntax():
  print("Syntax: python smesher-plot-speed.py [options] <directory>")
  print()
  print("Options:")
  print("  --json              Output JSON")
  print("  --no-header         Do not print header")
  print("  --report            Send report to reports.smesh.cloud")
  print("  --report-force-cpu  Force CPU provider")
  print("  --report-force-gpu  Force GPU provider")
  print("  --version           Print version")
  print("  --help              Print help")
  print()
  print("Arguments:")
  print("  directory      The directory containing postdata_metadata.json, smeshing_metadata.json, and postdata_*.bin files")
  print()

def post_report(data):
  headers = { 'Content-Type': 'application/json' }
  request = urllib.request.Request(url='https://reports.smesh.cloud/api/reports/receive', method='POST')
  request.add_header('Content-Type', 'application/json')
  request.add_header('User-Agent', 'smesher-plot-speed')
  response = urllib.request.urlopen(request, json.dumps(data).encode())
  _content = response.read()

  if response.status == 200:
    data['report'] = {
      'sent': True
    }
  else:
    data['report'] = {
      'sent': False,
      'status_code': response.status_code,
      'reason': response.reason
    }
  return data

parse_arguments()
detect_cpu()
detect_os()
detect_gpus()
detect_provider()

if print_header:
  print(f"Smesher Plot Speed v{version} ({github_url})")
  print()
  print_cpu_info()
  print_gpu_info()
  print_provider_info()
  print_os_info()
  print()

directory = sys.argv[1]
if not os.path.isdir(directory):
    print("The provided directory does not exist.")
    sys.exit(1)

postdata = postdata_metadata()
smeshing = {}
files = postdata_bin_files(directory)
current_post_size_GiB = calculate_current_post_size_GiB(directory)

files_by_mod_time_desc = sorted(files, key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)
files_by_size = sorted(files, key=lambda x: os.path.getsize(os.path.join(directory, x)), reverse=True)

first_file = None
first_file_size = 0
total_size = 0
most_recent_complete_file = None
most_recent_complete_file_size = None
most_recent_time_delta_string = None
previous_most_recent_complete_file = None
previous_most_recent_complete_file_size = None

# Check if at least two files exist
if len(files_by_mod_time_desc) >= 2:
  complete_files = [file for file in files_by_mod_time_desc if os.path.getsize(os.path.join(directory, file)) == postdata['max_file_size']]
  first_file = os.path.join(directory, files_by_mod_time_desc[-1])
  previous_most_recent_complete_file = os.path.join(directory, complete_files[1])
  most_recent_complete_file = os.path.join(directory, complete_files[0])
  current_file = os.path.join(directory, files_by_mod_time_desc[0])

  first_file_size = os.path.getsize(first_file)
  most_recent_complete_file_size = os.path.getsize(most_recent_complete_file)
  current_size = os.path.getsize(current_file)

  # Get the total size of the files in the directory except the first file in the list
  total_size = 0
  for file in files_by_mod_time_desc[:-1]:
    file_path = os.path.join(directory, file)
    total_size += os.path.getsize(file_path)

# Calculate the time difference and throughput if both files are found
if first_file is not None and most_recent_complete_file is not None and current_file is not None:
  now = datetime.datetime.now().timestamp()
  first_time = os.path.getmtime(first_file)
  current_time = os.path.getmtime(current_file)
  first_time_diff = abs(current_time - first_time)
  current_time_diff = abs(now - current_time)
  most_recent_time = os.path.getmtime(most_recent_complete_file)
  previous_most_recent_complete_file_time = os.path.getmtime(previous_most_recent_complete_file)

  time_since_first = abs(now - first_time)
  time_since_current = abs(now - current_time)
  time_since_previous_most_recent = abs(now - previous_most_recent_complete_file_time)
  time_since_most_recent = abs(now - most_recent_time)
  time_between_most_recent_and_current = abs(current_time - most_recent_time)

  if current_file == most_recent_complete_file:
    print(f"PoST generation is complete!")
    print()
    progress_percent = 100
    remaining_post_size_GiB = 0
    throughput_MiBps = 0
    recent_throughput_MiBps = 0
    recent_etf_string = ""
    efd = None
    size_MiB = (total_size - first_file_size) / (1024 * 1024)  # Convert size to MiB
    throughput_MiBps = size_MiB / first_time_diff
  else:
    # Calculate throughput in MiB/s
    size_MiB = (total_size - first_file_size) / (1024 * 1024)  # Convert size to MiB
    throughput_MiBps = size_MiB / first_time_diff

    most_recent_complete_file_size = os.path.getsize(most_recent_complete_file)
    recent_size_MiB = (current_size) / (1024 * 1024)
    recent_throughput_MiBps = recent_size_MiB / time_between_most_recent_and_current
    #print(f"size_MiB {size_MiB}")
    #print(f"throughput_MiBps {throughput_MiBps}")
    #print(f"recent_size_MiB {recent_size_MiB}")
    #print(f"recent_throughput_MiBps {recent_throughput_MiBps}")

    # Calculate time difference in minutes and seconds
    first_minutes, first_seconds = divmod(first_time_diff, 60)
    first_minutes = int(first_minutes)  # Convert minutes to integer
    first_seconds = int(first_seconds)  # Convert seconds to integer
    first_time_delta_string = f"{first_minutes:02d}m {first_seconds:02d}s"

    most_recent_minutes, most_recent_seconds = divmod(time_since_most_recent, 60)
    most_recent_minutes = int(most_recent_minutes)  # Convert minutes to integer
    most_recent_seconds = int(most_recent_seconds)  # Convert seconds to integer
    most_recent_time_delta_string = f"{most_recent_minutes:02d}m {most_recent_seconds:02d}s"

    progress_percent = current_post_size_GiB / postdata['total_post_size_GiB'] * 100

    # estimated time to finish
    remaining_post_size_GiB = postdata['total_post_size_GiB'] - current_post_size_GiB
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

  print_output()
else:
  print("There are not enough files in the directory yet. Will calculate once the first two files complete.")
