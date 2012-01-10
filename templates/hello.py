# Author: Firstname Lastname
# License: BSD-2-Clause
# Version: 0.9
'''
Hello World PyMOL Plugin

Here goes the description of this fancy PyMOL plugin. To test it, save it as
"hello.py" and install it.
'''

def hello_world():
    '''
    This dummy says "Hello World" in a popup.
    '''
    from pymolplugins import pref_get
    foo = pref_get('hello.foo', 'default')

    import tkMessageBox
    tkMessageBox.showinfo('Hello World', 'Value of hello.foo: ' + str(foo))

def __init_plugin__(pmgapp):
    '''
    Initialization function (optional).
    '''
    from pymolplugins import addmenuitem
    addmenuitem('Hello World', hello_world)

def settings_dialog():
    '''
    Open a settings dialog (optional). If such a function is provided,
    show a "Settings" button for this plugin in the plugin manager.
    '''
    from pymolplugins import pref_get, pref_set
    foo = pref_get('hello.foo', 'default')

    import tkSimpleDialog
    foo = tkSimpleDialog.askstring('Settings', 'New value of hello.foo', initialvalue=foo)

    if foo is not None:
        pref_set('hello.foo', foo)

# vi:expandtab:smarttab:sw=4:ft=python
