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

def get_release_description(version):
    if version.startswith("v"):
        version = version[1:]

    release_description = ""
    found = False
    with open("CHANGELOG.md", "r") as f:
        for line in f.readlines():
            if not found and line.strip() == f"# {version}":
                found = True
            elif found and line.startswith("# "):
                break
            if found:
                release_description += f"{line}"
    return release_description


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract description of a release from CHANGELOG.md")
    parser.add_argument("version", help="Version number")
    args = parser.parse_args()

    print(get_release_description(args.version))
