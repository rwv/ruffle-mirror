import urllib.request
import json
import tempfile
import os
import zipfile
import subprocess
import re

package_json_template = os.path.abspath('./package.json')

def publish_release(release, dryrun=True):
    tag_name = release['tag_name']
    print(f'handle release {tag_name}')
    self_hosted_asset = list(filter(lambda x: 'selfhosted' in x['name'], release['assets']))[0]

    # generate temp dir for publish
    temp_folder = tempfile.TemporaryDirectory()
    temp_folder_path = temp_folder.name
    os.chdir(temp_folder_path)

    # write package.json to temp dir
    with open(package_json_template) as f:
        package_config = json.load(f)

    version = generate_version(tag_name)
    if not re.match(r'\d{4}\.\d{1,2}\.\d{1,2}', version):
        print('version error')
        return

    package_config['version'] = tag_name.strip('nightly-').replace('-', '.')

    with open(os.path.join(temp_folder_path, 'package.json'), mode='w') as f:
        f.write(json.dumps(package_config))

    # downlod asset file and unzip it
    zip_temp_folder = tempfile.TemporaryDirectory()
    zip_temp_folder_path = zip_temp_folder.name
    zip_file_path = os.path.join(zip_temp_folder_path, self_hosted_asset["name"])
    urllib.request.urlretrieve(self_hosted_asset['browser_download_url'], zip_file_path)
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(temp_folder_path)

    # publish to npm
    if dryrun:
        subprocess.run(["npm", "publish", "--dry-run"])
    else:
        subprocess.run(["npm", "publish"])

def get_all_npm_versions():
    versions_str = subprocess.check_output(['npm', 'view', 'ruffle-mirror', 'versions', '--json']).decode()
    versions = json.loads(versions_str)
    return versions

def generate_version(tag_name):
    try:
        version = tag_name.strip('nightly-').replace('-', '.')
        assert re.match(r'\d{4}\.\d{1,2}\.\d{1,2}', version)
        return version
    except Exception as e:
        print(f'Failed to convert {tag_name}\n{e}')
        return tag_name


if __name__ == '__main__':
    contents = urllib.request.urlopen("https://api.github.com/repos/ruffle-rs/ruffle/releases").read()
    releases = json.loads(contents)

    # only publish not published versions
    published_versions = get_all_npm_versions()
    releases_not_published = list(filter(lambda release: generate_version(release['tag_name']) not in published_versions, releases))

    for release in releases_not_published:
        publish_release(release, dryrun=False)
