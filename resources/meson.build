gnome = import('gnome')
i18n = import('i18n')

gnome.compile_resources(
    'flow',
    'flow.gresource.xml',
    gresource_bundle: true,
    install: true,
    install_dir: pkgdatadir,
)

subdir('icons')

install_data('com.github.essmehdi.flow.gschema.xml',
    install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

# Setup & verify desktop entry
desktop_file = i18n.merge_file(
    input: configure_file(
        input: 'com.github.essmehdi.flow.desktop.in.in',
        output: 'com.github.essmehdi.flow.desktop.in',
        configuration: {
            'appname': app_name,
            'appid': app_id,
        }
    ),
    type: 'desktop',
    po_dir: '../po',
    output: 'com.github.essmehdi.flow.desktop',
    install: true,
    install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_validate = find_program('desktop-file-validate', required: false)
if desktop_validate.found()
  test('Validate desktop file', desktop_validate,
    args: [desktop_file]
  )
endif

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
    test('Validate schema file', compile_schemas,
        args: ['--strict', '--dry-run', meson.current_source_dir()]
    )
endif