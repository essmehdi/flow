python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

sources = [
    '__init__.py',
    'main.py',
    'settings.py',
    'status_manager.py',
    'utils.py',
    'download.py',
    'controller.py',
    'toaster.py',
    'notifier.py',
    'about.py'
]

install_data(sources, install_dir: moduledir)
subdir('components')
subdir('preferences')
