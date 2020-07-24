from aqt import mw


def gc(arg, fail=False):
    conf = mw.addonManager.getConfig(__name__)
    if conf:
        return conf.get(arg, fail)
    else:
        return fail


def wcs(key, newvalue, addnew=False):
    config = mw.addonManager.getConfig(__name__)
    if not (key in config or addnew):
        return False
    else:
        config[key] = newvalue
        mw.addonManager.writeConfig(__name__, config)
        return True


# mw.addonManager.writeConfig writes a json file to disc, calling it repeatedly might slow
# down Anki?
def wcm(list_):
    config = mw.addonManager.getConfig(__name__)
    success = True
    for i in list_:
        key = i[0]
        newvalue = i[1]
        if len(i) == 3:
            addnew = i[2]
        else:
            addnew = False
        if not (key in config or addnew):
            success = False
        else:
            config[key] = newvalue
    mw.addonManager.writeConfig(__name__, config)
    return success
