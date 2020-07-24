from aqt import mw

from anki.hooks import addHook


# check and maybe transform config.json: old V3 to tableaddon_configlevel_2020-04-27
def maybe_adjust_config():
    conf = mw.addonManager.getConfig(__name__)
    if not conf:
        return
    if conf.get("tableaddon_configlevel_2020-04-27", None):
        return
    if not "table_style_css_V3" in conf:
        return
    styling = conf.get("table_style_css_V3")
    originalstyling = styling.copy()
    if not isinstance(styling, dict):
        return
    newnames = {
        "less ugly - full width": "basic - full width",
        "less ugly - minimal width": "basic - minimal width",       
    }
    for name in list(styling):
        if name in newnames:
            styling[newnames.get(name)] = styling.pop(name)            
    newvalues = {
        "basic - full width": {
            "old": " style='font-size: 85%; width: 100%; border-collapse: collapse; border: 1px solid black;' ",
            "new": " class='table_class_basic_full_width' style='font-size: 85%; width: 100%; border-collapse: collapse; border: 1px solid;' "
        },
        "basic - minimal width": {
            "old": " style='font-size: 85%; border-collapse: collapse; border: 1px solid black;' ",
            "new": " class='table_class_basic_minimal_width' style='font-size: 85%; border-collapse: collapse; border: 1px solid;' "
        },
        "no outside border": {
            "old": " style='font-size: 85%; width: 100%; border-style: hidden; border-collapse: collapse;' ",
            "new": " class='table_class_no_outside_border' style='font-size: 85%; width: 100%; border-style: hidden; border-collapse: collapse;' "
        },
        "pfp - style": {
            "old": " style='font-size: 95%; width: 100%; border-collapse: collapse;' ",
            "new": " class='table_class_pfp_style' style='font-size: 95%; width: 100%; border-collapse: collapse;' "
        }
    }
    for key in list(styling):
        if key in newvalues:
            vals = styling.get(key, None)
            if vals and isinstance(vals, dict) and "TABLE_STYLING" in vals:
                if vals["TABLE_STYLING"] == newvalues[key]["old"]:
                    styling[key]["TABLE_STYLING"] = newvalues[key]["new"]

    default = conf.get("table_style__default", None)
    if default:
        for old, new in newnames.items():
            if default == old:
                conf["table_style__default"] = new

    conf["tableaddon_configlevel_2020-04-27"] = True
    mw.addonManager.writeConfig(__name__, conf)
addHook('profileLoaded', maybe_adjust_config)