project('flow', version: '0.1.0',)

fs = import('fs')

profile = get_option('profile')
app_name = 'Flow'
app_id = 'com.github.essmehdi.flow'
v_suffix = ''

if profile == 'development'
  app_name = app_name + ' (Devel)'
  app_id = app_id + '.devel'
  if fs.is_dir('.git')
    git_rev = run_command('git', 'rev-parse', '--short', 'HEAD', check: false).stdout().strip()
    if git_rev != ''
      v_suffix = '-@0@'.format(git_rev)
    endif
  endif
endif

pymod = import('python')
pymod.find_installation('python3')

dependency('gtk4')
dependency('libadwaita-1')
dependency('libcurl')

# Separate release data from devel data
folder_suffix = ''
if profile == 'development'
  folder_suffix = '-devel'
endif
pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'flow')

subdir('resources')
subdir('flow')
subdir('extension')
subdir('po')

import('gnome').post_install(
  glib_compile_schemas: true,
  gtk_update_icon_cache: true,
  update_desktop_database: true
)