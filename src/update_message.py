import os

from aqt.utils import (
    showInfo,
    tooltip
)

from .config import gc, wcs
from .update_config import default_v3_from_april_2020


addon_path = os.path.dirname(__file__)
addonfoldername = os.path.basename(addon_path)
user_files = os.path.join(addon_path, "user_files")


def maybe_show_update_message_for_2020_07_24():
    update_message_2020_07_24 = "update_2020-07-24"
    addonname = "Add Table"
    fa = os.path.join(user_files, update_message_2020_07_24)
    if os.path.isfile(fa):
        return
    if not os.path.isdir(user_files):
        os.makedirs(user_files)
    open(fa, 'a').close()
    wcs("tableaddon_configlevel_2020-07-24", True, True)  # for future compatibility also store this.
    if gc("table_style_css_V3") == default_v3_from_april_2020:
        # the user didn't change the config, so no reason to bother:
        return
    msg = f"""
This is a one-time message from the add-on "<b>{addonname}</b>".
<br><br>
It's shown one time because you just installed it or just upgraded. If you installed this 
add-on for the first time this message is not relevant for you.
<br><br>
The rest of this message talks about the configuration of the add-on "{addonname}". If like most
people you never changed the config or only changed the shortcut to insert the table the rest
of the message is not relevant for you.
<br><br>
You can see the config for an add-on like this: In the main window menu bar click on "Tools", then on
"Add-ons". In the window that opens select the add-on "{addonname}" and then click the button
"Config" in the lower right of this add-on.
<br><br>
If you ever changed config settings named "table_style_css", "table_style_css_V2" or 
"table_style_css_V3" check the 
<a href="https://ankiweb.net/shared/info/1237621971" rel="nofollow">description on ankiweb</a>
in the section "Update notice".
    """
    showInfo(msg, textFormat="rich")
maybe_show_update_message_for_2020_07_24()
