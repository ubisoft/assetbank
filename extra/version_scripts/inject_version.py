import os
import subprocess
import re


def get_version():
    cp = subprocess.run(
        ["git", "describe", "--tags", "--dirty", "--match=v*"],
        stdout=subprocess.PIPE,
        check=True,
    )
    version = str(cp.stdout, encoding="utf8").strip()

    version_tokens = version.split("-")
    if len(version_tokens) == 1:
        return version_tokens[0]
    return version_tokens[0] + "+" + "-".join(version_tokens[1:])


def main():
    version = get_version()

    pyproject_file = "pyproject.toml"
    new_projectfile_str = ""
    with open(pyproject_file, "r") as fp:
        new_projectfile_str = re.sub(r'\[tool\.poetry\]([\s\S]*)version *= *\"(.*)\"', rf'[tool.poetry]\g<1>version = "{version}"', fp.read())

    with open(pyproject_file, "w") as fp:
        fp.write(new_projectfile_str)

    version_numbers = [
        int(n) for n in version[1:].split("+")[0].split("-")[0].split(".")
    ]
    if "+" in version:
        commit_version_str = version[1:].split("+")[1].split("-")[0]
        if commit_version_str != "dirty":
            version_numbers += [int(commit_version_str)]

    init_file = os.path.join("uas_assetbank", "__init__.py")
    new_init_file_str = ""
    with open(init_file, "r") as fp:
        new_init_file_str = re.sub(r'bl_info([\s\S]*)\"version\" *: *(\(.*\))', rf'bl_info\g<1>"version": {str(tuple(version_numbers))}', fp.read())

    with open(init_file, "w") as fp:
        fp.write(new_init_file_str)


if __name__ == "__main__":
    main()
