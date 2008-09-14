import gettext

def dummy(str):
    return str

once = False

if not once:
    try:
        t = gettext.translation('pythm', 'locale')
        _ = t.lgettext
        once = True
    except Exception,e:
        print "No Locale found, falling back! Error was:" + str(e) 
        _ = dummy
        once = True
    

