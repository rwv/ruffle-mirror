import urllib.request
import json
import tempfile
import os
import subprocess
import re
import tarfile

PACKAGE_JSON_TEMPLATE = os.path.abspath('./package.json')
ROOT_PATH = os.path.abspath('.')

def get_all_npm_ruffle_versions():
    versions_str = subprocess.check_output(['npm', 'view', '@ruffle-rs/ruffle', 'versions', '--json']).decode()
    versions = json.loads(versions_str)
    # filter out versions with date in them
    versions = list(filter(lambda x: re.search(r'\d{4}\.\d{1,2}\.\d{1,2}', x), versions))
    # extract date from versions
    extract_date = lambda ver: re.search(r'\d{4}\.\d{1,2}\.\d{1,2}', ver).group(0)
    versions_dict = {extract_date(version): version for version in versions}
    return versions_dict

def get_all_ruffle_mirror_versions():
    versions_str = subprocess.check_output(['npm', 'view', 'ruffle-mirror', 'versions', '--json']).decode()
    versions = json.loads(versions_str)
    return versions

def publish_release(ruffle_version, version_to_publish):
    # generate temp dir for publish
    temp_folder = tempfile.TemporaryDirectory()
    temp_folder_path = temp_folder.name

    # download ruffle dist
    dist_url = subprocess.check_output(['npm', 'view', f'@ruffle-rs/ruffle@{ruffle_version}', 'dist.tarball']).decode()
    print(f'Downloading ruffle-{ruffle_version}: {dist_url}')
    dist_temp_folder = tempfile.TemporaryDirectory()
    urllib.request.urlretrieve(dist_url, os.path.join(dist_temp_folder.name, 'ruffle.tar.gz'))

    # untar ruffle dist
    with tarfile.open(os.path.join(dist_temp_folder.name, 'ruffle.tar.gz'), 'r:gz') as tar:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, temp_folder_path)

    # write package.json to temp dir
    with open(PACKAGE_JSON_TEMPLATE) as f:
        package_config = json.load(f)

    package_config['version'] = version_to_publish
    with open(os.path.join(temp_folder_path, 'package', 'package.json'), mode='w') as f:
        json.dump(package_config, f, indent=2)

    # publish to npm
    os.chdir(os.path.join(temp_folder_path, 'package'))
    subprocess.run(["npm", "publish"])
    os.chdir(ROOT_PATH)

def main():
    # get versions to publish
    ruffle_versions = get_all_npm_ruffle_versions()
    ruffle_mirror_versions = get_all_ruffle_mirror_versions()
    versions_to_publish = list(set(ruffle_versions.keys()) - set(ruffle_mirror_versions))
    versions_to_publish.sort(key=lambda x: list(ruffle_versions.keys()).index(x))
    print(f'Versions to publish: {versions_to_publish}')
    for version in versions_to_publish:
        print(f'Publishing {version}')
        publish_release(ruffle_versions[version], version)

if __name__ == '__main__':
    main()