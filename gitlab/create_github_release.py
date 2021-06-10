# GPLv3 License
#
# Copyright (C) 2020 Ubisoft
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--tag", "-t", help="tag name", required=True)
parser.add_argument("--name", "-n", help="release name", required=True)
parser.add_argument("--zip", "-z", help="zip path to upload", required=True)
args = parser.parse_args()

import os
import sys

access_token = os.environ.get("K8S_SECRET_GITHUB_ACCESS_TOKEN")
if access_token is None:
    sys.exit("Unable to retrieve GitHub access token from environment variables.")

repo_name = os.environ.get("GITHUB_MIRROR")
if repo_name is None:
    sys.exit("Unable to retrieve Github repository name from environment variables.")

from .get_release_description import get_release_description
message = get_release_description(args.tag)

from github import Github
github = Github(access_token)
repo = github.get_repo(repo_name)
release = repo.create_git_release(args.tag, args.name, message)
release.upload_asset(args.zip, label="", content_type="application/zip", name=f"AssetBank_{args.tag}.zip")
