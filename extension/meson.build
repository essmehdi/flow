fs = import('fs')

configure_file(
    input: 'host.py.in',
    output: 'flow-connector',
    configuration: conf,
    install: true,
    install_dir: get_option('bindir')
)

if fs.is_dir('/usr/lib/mozilla/native-messaging-hosts')
    install_data(
        'com.github.essmehdi.flow.json',
        install_dir: '/usr/lib/mozilla/native-messaging-hosts'
    )
endif

if fs.is_dir('/etc/opt/chrome/native-messaging-hosts')
    install_data(
        'com.github.essmehdi.flow.json',
        install_dir: '/etc/opt/chrome/native-messaging-hosts'
    )
endif