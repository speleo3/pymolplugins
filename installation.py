'''
PyMOL Plugins Engine, Installation Routines

(c) 2011-2012 Thomas Holder, PyMOL OS Fellow
License: BSD-2-Clause

'''

import os

# supported file types for installation. Do not support pyc and pyo binaries,
# we want text files that can be parsed for metadata.
zip_extensions = ['zip', 'tar.gz']
supported_extension = ['py'] + zip_extensions

def get_default_user_plugin_path():
    '''
    User plugin directory defaults to ~/.pymol/startup on Linux and to
    %APPDATA%\pymol\startup on windows.
    '''
    if 'APPDATA' in os.environ:
        return os.path.join(os.environ['APPDATA'], 'pymol', 'startup')
    return os.path.expanduser('~/.pymol/startup')

def is_writable(dirname):
    '''
    Return True if directory is writable.
    '''
    path = os.path.join(dirname, '__check_writable')
    try:
        f = open(path, 'wb')
        f.close()
        os.remove(path)
        return True
    except (IOError, OSError):
        return False

def installPluginFromFile(ofile):
    '''
    Install plugin from file.

    Takes python (.py) files and archives which contain a python module.
    '''
    from . import get_startup_path
    from .legacysupport import get_tk_root

    plugdirs = get_startup_path()
    if len(plugdirs) == 1:
        installPluginFromFile2(ofile, plugdirs[0])
        return

    def plugdir_callback(result):
        if result == 'OK':
            s = dialog.getcurselection()
            if len(s) == 0:
                return False
            installPluginFromFile2(ofile, s[0])
        dialog.destroy()

    import Pmw
    dialog = Pmw.SelectionDialog(get_tk_root(), title='Select plugin directory',
            buttons = ('OK', 'Cancel'), defaultbutton='OK',
            scrolledlist_labelpos='n',
            label_text='In which directory should the plugin be installed?',
            scrolledlist_items=plugdirs,
            command=plugdir_callback)
    dialog.component('scrolledlist').selection_set(0)

def installPluginFromFile2(ofile, plugdir):
    '''
    Continuation from installPluginFromFile
    '''
    import shutil
    from . import startup, PluginInfo, showinfo, askyesno
    from . import get_startup_path, set_startup_path

    if not is_writable(plugdir):
        user_plugdir = get_default_user_plugin_path()
        if not askyesno('Warning',
                'Unable to write to the plugin directory.\n'
                'Should a user plugin directory be created at\n' + user_plugdir + '?'):
            showinfo('Error', 'Installation aborted')
            return

        if not os.path.exists(user_plugdir):
            try:
                os.makedirs(user_plugdir)
            except OSError:
                showinfo('Error', 'Could not create user plugin directory')
                return

        plugdir = user_plugdir

    plugdirs = get_startup_path()
    if plugdir not in plugdirs:
        set_startup_path([plugdir] + plugdirs)

    basename = os.path.basename(ofile)
    name, _, ext = basename.partition('.')

    # ext may contain version numbers or multiple extensions
    if '.tar' in ext:
        ext = 'tar' + ext.lower().rsplit('.tar', 1)[-1]
    else:
        ext = ext.rsplit('.', 1)[-1].lower()

    if ext not in supported_extension:
        showinfo('Error', 'Not a valid plugin file, installation cancelled!')
        return

    def remove_if_exists(pathname):
        if not os.path.exists(pathname):
            return

        # TODO: check and compare version

        is_dir = os.path.isdir(pathname)
        if is_dir:
            msg = 'Directory "%s" already exists, overwrite?' % pathname
        else:
            msg = 'File "%s" already exists, overwrite?' % pathname
        ok = askyesno('Confirm', msg)
        if not ok:
            raise UserWarning('will not overwrite "%s"' % pathname)
        if is_dir:
            shutil.rmtree(pathname)
        else:
            os.remove(pathname)

    try:
        if ext in zip_extensions:
            # import archive

            # TODO: better first extract to temporary directory and then
            # install from there

            if ext == 'zip':
                import zipfile
                zf = zipfile.ZipFile(ofile)
            else:
                import tarfile
                zf = tarfile.open(ofile)
                zf.namelist = zf.getnames
            # make sure pathnames are not absolute
            cwd = os.getcwd()
            namelist = zf.namelist()
            for f in namelist:
                f = os.path.normpath(f)
                if not os.path.abspath(f).startswith(cwd):
                    raise UserWarning('ZIP file contains absolute path names')
            # analyse structure
            namedict = dict()
            for f in namelist:
                x = namedict
                for part in f.split(os.sep):
                    if part != '':
                        x = x.setdefault(part, {})
            if len(namedict) == 0:
                raise UserWarning('Archive empty.')
            name = namedict.keys()[0]
            if '.' in name or len(namedict) != 1:
                raise UserWarning('Archive must contain a single directory.')
            if '__init__.py' not in namedict[name]:
                raise UserWarning('Missing %s.__init__.py' % (name))
            # install
            mod_dir = os.path.join(plugdir, name)
            mod_file = os.path.join(mod_dir, '__init__.py')
            remove_if_exists(mod_dir)
            zf.extractall(plugdir)

        elif name == '__init__':
            # import directory
            odir = os.path.dirname(ofile)
            name = os.path.basename(odir)
            mod_dir = os.path.join(plugdir, name)
            remove_if_exists(mod_dir)
            shutil.copytree(odir, mod_dir)

            mod_file = os.path.join(mod_dir, '__init__.py')

        elif ext == 'py':
            # import python file
            mod_file = os.path.join(plugdir, name + '.py')
            remove_if_exists(mod_file)
            shutil.copy(ofile, mod_file)

        else:
            raise UserWarning('this should never happen')

    except:
        from . import verbose
        if verbose:
            import traceback
            traceback.print_exc()
        showinfo('Error', 'unable to install plugin "%s"' % name)
        return

    prefix = startup.__name__
    info = PluginInfo(name, prefix + '.' + name, mod_file)

    if info.load(force=1):
        showinfo('Success', 'Plugin "%s" has been installed.' % name)
    else:
        showinfo('Error', 'Plugin "%s" has been installed but initialization failed.' % name)

# vi:expandtab:smarttab:sw=4
