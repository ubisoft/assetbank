from extra.version_scripts.inject_version import main as inject_version, get_version

import argparse
import subprocess


def main():
    cp = subprocess.run(["git", "tag", "-l", "v*"], stdout=subprocess.PIPE, check=True)
    tags_str = str(cp.stdout, encoding="utf8").strip()
    all_tags = set(tags_str.split("\n")) if tags_str != '' else set()

    if len(all_tags) > 0:
        version = get_version()
        if "dirty" in version:
            print("Please commit or discard/stash your changes before running this script.")
            exit(1)

        print(f"Current version: {version}")

    parser = argparse.ArgumentParser(
        description="Set a new version number for the project."
    )

    parser.add_argument("major", type=int, help="Major version number")
    parser.add_argument("minor", type=int, help="Minor version number")
    parser.add_argument("bugfix", type=int, help="Bugfix version number")
    parser.add_argument("message", type=str, help="Message for version tag")

    args = parser.parse_args()

    version_string = f"{args.major}.{args.minor}.{args.bugfix}"
    tag_name = f"v{version_string}"

    if tag_name in all_tags:
        print(f"Version tag {tag_name} already defined.")
        exit(1)

    subprocess.run(["git", "tag", tag_name], check=True)
    inject_version()
    subprocess.run(["auto-changelog", "--tag-prefix=v"], check=True)
    cp = subprocess.run(["git", "status", "-s", "-uno"], stdout=subprocess.PIPE, check=True)
    if str(cp.stdout, encoding="utf8").strip() != "":
        # Only if something has changed according to git status:
        subprocess.run(["git", "commit", "-a", "-m", f"Update version to {version_string}"], check=True)
        subprocess.run(["git", "tag", "-f", tag_name, "-m", f"Version {version_string}"], check=True)
    
    version = get_version()
    print(f"New version: {version}")

if __name__ == "__main__":
    main()
