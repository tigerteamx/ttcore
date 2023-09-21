def up_version(content):
    versions_levels = content.strip().split(".")
    level_1, level_2, level_3 = versions_levels
    level_1, level_2, level_3 = int(level_1), int(level_2), int(level_3)

    if level_3 <= 100:
        return f"{level_1}.{level_2}.{level_3 + 1}"

    if level_2 <= 10:
        return f"{level_1}.{level_2 + 1}.1"

    return f"{level_1 + 1}.1.1"


if __name__ == "__main__":
    with open("VERSION.txt", "r+") as f:
        version = f.read().strip()
        next_version = up_version(version)
        f.seek(0)
        f.truncate()
        f.write(next_version)
