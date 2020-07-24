from aqt import mw

from anki.hooks import addHook

from .config import gc, wcs, wcm


# check and maybe transform config.json: old V3 to tableaddon_configlevel_2020-04-27
def adjust_to_20200427(conf):
    styling = gc("table_style_css_V3")
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
    return conf


default_v3_from_april_2020 = {
        "css1": {
            "BODY_STYLING": "",
            "HEAD_STYLING": "",
            "TABLE_STYLING": " class='table_class_one' "
        },
        "css2": {
            "BODY_STYLING": "",
            "HEAD_STYLING": "",
            "TABLE_STYLING": " class='table_class_two' "
        },
        "basic - full width": {
            "BODY_STYLING": " style='{0} padding: 2px; border: 1px solid;' ",
            "HEAD_STYLING": " style='{0} padding: 2px; border: 1px solid;' ",
            "TABLE_STYLING": " class='table_class_basic_full_width' style='font-size: 85%; width: 100%; border-collapse: collapse; border: 1px solid;' "
        },
        "basic - minimal width": {
            "BODY_STYLING": " style='{0} padding:2px; border: 1px solid;' ",
            "HEAD_STYLING": " style='{0} padding:2px; border: 1px solid;' ",
            "TABLE_STYLING": " class='table_class_basic_minimal_width' style='font-size: 85%; border-collapse: collapse; border: 1px solid;' "
        },
        "no outside border": {
            "BODY_STYLING": " style='{0} padding: 2px; border: 1px solid' ",
            "HEAD_STYLING": " style='{0} padding: 2px; border: 1px solid' ",
            "TABLE_STYLING": " class='table_class_no_outside_border' style='font-size: 85%; width: 100%; border-style: hidden; border-collapse: collapse;' "
        },
        "pfp - style": {
            "BODY_STYLING": " style='{0} padding: 5px; border-bottom: 1px solid #B0B0B0' ",
            "HEAD_STYLING": " style='{0} padding: 5px; border-bottom: 2px solid #00B3FF' ",
            "TABLE_STYLING": " class='table_class_pfp_style' style='font-size: 95%; width: 100%; border-collapse: collapse;' "
        },
        "unstyled": {
            "BODY_STYLING": "",
            "HEAD_STYLING": "",
            "TABLE_STYLING": ""
        }
    }


default_v3_from_july_2020 = {
        "css1": {
            "BODY_STYLING": "",
            "HEAD_STYLING": "",
            "TABLE_STYLING": " class='table_class_one' "
        },
        "css2": {
            "BODY_STYLING": "",
            "HEAD_STYLING": "",
            "TABLE_STYLING": " class='table_class_two' "
        },
        "basic - full width": {
            "BODY_STYLING": " style='{0} padding: 2px; border: 1px solid;' ",
            "HEAD_STYLING": " style='{0} padding: 2px; border: 1px solid;' ",
            "TABLE_STYLING": " class='table_class_basic_full_width' style='font-size: 85%; width: 100%; border-collapse: collapse; border: 1px solid;' "
        },
        "basic - minimal width": {
            "BODY_STYLING": " style='{0} padding:2px; border: 1px solid;' ",
            "HEAD_STYLING": " style='{0} padding:2px; border: 1px solid;' ",
            "TABLE_STYLING": " class='table_class_basic_minimal_width' style='font-size: 85%; border-collapse: collapse; border: 1px solid;' "
        },
        "no outside border": {
            "BODY_STYLING": " style='{0} padding: 2px; border: 1px solid' ",
            "HEAD_STYLING": " style='{0} padding: 2px; border: 1px solid' ",
            "TABLE_STYLING": " class='table_class_no_outside_border' style='font-size: 85%; width: 100%; border-style: hidden; border-collapse: collapse;' "
        },
        "pfp - style": {
            "BODY_STYLING": " style='{0} padding: 5px; border-bottom: 1px solid #B0B0B0' ",
            "HEAD_STYLING": " style='{0} padding: 5px; border-bottom: 2px solid #00B3FF' ",
            "TABLE_STYLING": " class='table_class_pfp_style' style='font-size: 95%; width: 100%; border-collapse: collapse;' "
        },
        "unstyled": {
            "BODY_STYLING": "",
            "HEAD_STYLING": "",
            "TABLE_STYLING": ""
        }
    }



def maybe_adjust_config():
    conf = mw.addonManager.getConfig(__name__)
    if not conf:
        return
    # add classes to add-ons config from after 2019-11-07 (v3). This update code was 
    # introduced in 2020-04-24
    if not conf.get("tableaddon_configlevel_2020-04-27"):
        if "table_style_css_V3" in conf:
            conf = adjust_to_20200427(conf)
    # remove black border. This update code was introduced in 2020-07-24.
    if conf.get("tableaddon_configlevel_2020-04-27"):
        if conf.get("table_style_css_V3") == default_v3_from_april_2020:
            wcm([["table_style_css_V3", default_v3_from_july_2020]])
# DONT AUTOUPDATE ANYMORE. NOT WORTH THE TIME TO MAKE SURE ITS RISKFREE.
# addHook('profileLoaded', maybe_adjust_config)


def minimal_adjust_config():
    default = gc("table_style__default")
    if default:
        legalnames = [key for key in gc("table_style_css_V4").keys()]
        if default not in legalnames:
            wcs("table_style__default", "basic - full width", True)
addHook('profileLoaded', minimal_adjust_config)
