import os
import time


addon_path = os.path.dirname(__file__)
addonfoldername = os.path.basename(addon_path)
user_files = os.path.join(addon_path, "user_files")
installed_at_file = os.path.join(user_files, "first_install_time")


if not os.path.isfile(installed_at_file):
    if not os.path.isdir(user_files):
        os.makedirs(user_files)
    with open(installed_at_file, "w") as f:
        now = int(time.time())
        f.write(str(now))
