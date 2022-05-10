conf = configuration_data()
conf.set('PYTHON', pymod.find_installation('python3').path())
conf.set('VERSION', meson.project_version() + v_suffix)
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)
conf.set('profile', profile)
conf.set('appname', app_name)
conf.set('appid', app_id)

configure_file(
  input: 'load.py.in',
  output: 'flow',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

sources = [
    '__init__.py',
    'main.py',
]

install_data(sources, install_dir: moduledir)

subdir('ui')
subdir('utils')
subdir('core')
