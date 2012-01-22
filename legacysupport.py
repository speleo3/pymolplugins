'''
PyMOL Plugins Engine, Legacy Support

This module overloads PyMOLs PMGApp class which so far handles plugin support.
It also provides a get_pmgapp() function that either returns the actual PMGApp
instance, or a fake instance with "root" and "menuBar" properties which can be
used if PMGApp has retired.

(c) 2011-2012 Thomas Holder, PyMOL OS Fellow
License: BSD-2-Clause

'''

import os
import pymol
from pmg_tk import startup, PMGApp

__all__ = [
    'startup',
    'get_pmgapp',
    'get_tk_root',
    'get_tk_focused',
]

def get_pmgapp():
    '''
    Returns the PMGApp instance.
    '''
    if pymol._ext_gui is None:
        pymol._ext_gui = createlegacypmgapp()
    return pymol._ext_gui

def get_tk_root():
    '''
    Returns the Tk master instance.
    '''
    return get_pmgapp().root

def get_tk_focused():
    '''
    Return the Tk widget which has currently the focus.
    '''
    root = get_tk_root()
    focused = root.focus_get()
    if focused is None:
        return root.focus_lastfor()
    return focused

def installPlugin(self):
    '''
    Overloaded version of pmg_tk.PMGApp.installPlugin

    Open dialog to install plugin
    '''
    from .installation import zip_extensions, installPluginFromFile

    # ask for file; to install a directory, point to its __init__.py file
    filetypes = [('Python Files', '*.py')] + \
            [('Archives', '*.' + ext) for ext in zip_extensions]
    filetypes = [('All Files', pattern) for (_, pattern) in filetypes] + filetypes
    ofile = tkFileDialog.askopenfilename(title='Install Plugin',
            initialdir=os.getcwd(),
            filetypes=filetypes)
    if len(ofile):
        installPluginFromFile(ofile)

def initializePlugins(self):
    '''
    Overloaded version of pmg_tk.PMGApp.initializePlugins

    Searches for plugins
    Registers PluginInfo instances
    Autoloads plugins
    '''
    from . import findPlugins, PluginInfo, addmenuitem

    for parent in [startup]:
        modules = findPlugins(parent.__path__)

        for name, filename in modules.iteritems():
            mod_name = parent.__name__ + '.' + name
            info = PluginInfo(name, mod_name, filename)
            if info.autoload:
                info.load(self)

    # Load plugin manager independent of other plugins
    def plugin_manager():
        from . import managergui
        managergui.manager_dialog()
    self.menuBar.deletemenuitems('PluginAction', 0, 2)
    addmenuitem('-', None, 'PluginAction')
    addmenuitem('Plugin Manager', plugin_manager, 'PluginAction')

def createlegacypmgapp():
    '''
    Start a Tk app in separate thread.

    Returns a "fake" PMGApp instance for legacy support
    '''
    app = pymol.Scratch_Storage()
    app.root = None
    app.menuBar = pymol.Scratch_Storage()
    app.menuBar.addmenuitem = lambda *x, **y: None
    app.menuBar.addcascademenu = lambda *x, **y: None

    def starttk():
        import Tkinter
        app.root = Tkinter.Tk()
        app.root.withdraw()
        app.root.mainloop()

    import threading
    t = threading.Thread(target=starttk, args=())
    t.setDaemon(1)
    t.start()

    import time
    wait, maxwait = 0.01, 1.0
    while app.root is None and maxwait > 0.0:
        time.sleep(wait)
        maxwait -= wait

    return app

# overload PMGApp methods
PMGApp.initializePlugins = initializePlugins
PMGApp.installPlugin = installPlugin

# wrappers for tkMessageBox and tkFileDialog that always use the current
# focused widget as parent

class _tkMessageBox(object):
    def __getattr__(self, name):
        import tkMessageBox as module
        wrapped = getattr(module, name)
        def dialog(title, message, parent=None, **kwargs):
            if parent is None:
                parent = get_tk_focused()
            print ' ' + title + ': ' + message
            return wrapped(title, message, parent=parent,  **kwargs)
        setattr(self, name, dialog)
        return dialog

class _tkFileDialog(object):
    def __getattr__(self, name):
        import tkFileDialog as module
        wrapped = getattr(module, name)
        def dialog(parent=None, *args, **kwargs):
            if parent is None:
                parent = get_tk_focused()
            return wrapped(*args, parent=parent,  **kwargs)
        setattr(self, name, dialog)
        return dialog

tkMessageBox = _tkMessageBox()
tkFileDialog = _tkFileDialog()

# vi:expandtab:smarttab:sw=4
