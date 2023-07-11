#!/usr/bin/env python3
#
## horn: hashicorp release notes
#
## usage:
#
## horn check  # idempotently get all the release notes from releases.hashicorp.com
## horn grep "prepared query failover to cluster peers never un-failing over"  # tabulate releases with this string
#
#######################################################################################################################

import requests
import re
from bs4 import BeautifulSoup
import sys
import os
import getopt

def usage():
  print(f"Usage: {sys.argv[0]} [-c] [-g pattern]")
  print("Options:")
  print("  -c         Check all tool releases")
  print("  -g         Search for a pattern in release notes")
  print("  -h         Show usage")

def get_release_notes(tool, version):
  # Construct the URL for the tool's releases page on GitHub
  print(f'Getting release notes for {tool} {version}')
  url = f"https://github.com/hashicorp/{tool}/releases/tag/v{version}"

  # Fetch the page HTML and parse it using BeautifulSoup
  response = requests.get(url)
  if response.status_code != 200:
    print(f'Error fetching {url}: HTTP {response.status_code}')
    return None

  soup = BeautifulSoup(response.content, "html.parser")

  # Find the release notes section and extract the text
  notes_section = soup.find("div", attrs={"data-test-selector": "body-content"})
  if not notes_section:
    print(f"No release notes found for {tool} {version}")
    return None

  notes_text = notes_section.get_text().strip()

  # Insert the full URL as the first line of the file
  notes_text = f"{url}\n\n{notes_text}"

  # Replace '(PR)' at the start of a line with '- PR'
  notes_text = notes_text.replace('\n(PR)', '\n- PR')

  # Create the directory for the release notes file if it does not exist
  subdir_path = os.path.expanduser(f'~/.horn/{tool}_{version}')
  os.makedirs(subdir_path, exist_ok=True)

  # Write the release notes to a file
  notes_file_path = os.path.join(subdir_path, f"{tool}_{version}_release_notes.txt")
  with open(notes_file_path, 'w') as f:
    f.write(notes_text)
    print(f'Release notes saved to {notes_file_path}')

  return notes_text

def get_all_releases():
  tools = ['boundary', 'waypoint']
  # tools = ['boundary', 'consul', 'nomad', 'packer', 'terraform', 'vault', 'vagrant']
  releases = []
  for tool in tools:
    print(f'{tool}...')
    url = f'https://releases.hashicorp.com/{tool}/'
    response = requests.get(url)
    if response.status_code != 200:
      print(f'Error fetching {url}: HTTP {response.status_code}')
      continue

    print(f'Soupifying {tool}')
    soup = BeautifulSoup(response.content, "html.parser")
    releases_list = soup.find_all("a", href=True)
    print(f'{tool} soup is {len(releases_list)} entries:')

    # latest_version = None
    for release in releases_list:
      if '..' not in release.text:
        version = release.text
        print(f'{version}')
        releases.append(version)

  return releases

def create_horn_subdirs(subdir_names):
    horn_dir = os.path.expanduser('~/.horn')
    if not os.path.exists(horn_dir):
        os.mkdir(horn_dir, mode=0o700)

    empty_subdirs = []
    for subdir_name in subdir_names:
        subdir_path = os.path.join(horn_dir, subdir_name)
        if not os.path.exists(subdir_path):
            os.mkdir(subdir_path, mode=0o700)
        elif not os.listdir(subdir_path):
            empty_subdirs.append(subdir_name)

    return empty_subdirs

def main():
  check_releases = False
  grep_pattern = None

  try:
    opts, args = getopt.getopt(sys.argv[1:], "cg:h")
  except getopt.GetoptError as err:
    print(str(err))
    usage()
    sys.exit(1)

  for opt, arg in opts:
    if opt == "-c":
      check_releases = True
    elif opt == "-g":
      grep_pattern = arg
    elif opt == "-h":
      usage()
      sys.exit(0)
    else:
      print(f'Unknown option: {opt}')
      usage()
      sys.exit(1)

  if check_releases:
      print(f'Updating local resources from online release note stores')
      releases = get_all_releases()
      new_releases = create_horn_subdirs(releases)
      for new_release in new_releases:
        print(f'Found empty release directory in my cache for: {new_release}')
        tool, version = new_release.split('_')
        get_release_notes(tool, version)
  if grep_pattern:
    for tool, version in releases.items():
      print(f'Searching release notes for {tool} v{version}...')
      notes = get_release_notes(tool, version)
      if notes and grep_pattern in notes:
        print(f'Found match for {grep_pattern} in {tool} v{version}')


if __name__ == "__main__":
    main()
