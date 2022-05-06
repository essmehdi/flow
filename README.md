# Flow - The download manager for GNOME

![](screenshots/1.png)

A utility application to automatically organize and keep track of your downloads designed for GNOME. This project is still in development.

This app aims to be an alternative for Internet Download Manager on Linux.

This download manager features basic download with cURL, auto-sorting based on file extension and resuming with new link for broken downloads. More features are coming.

## Browser extension

For now, it is only available for Firefox.

You can find the extension for Firefox [here](https://addons.mozilla.org/en-US/firefox/addon/flow-intercepter/).

## Installation

### Dependencies

You need to install some python dependencies from PIP: `validators` and `pycurl`. Run the command below to get them:

```shell
pip install validators pycurl
```

### Build from source

To build from source, clone this repository and build the project with Meson:

```shell
git clone https://gitlab.com/essmehdi/flow.git
cd flow
meson build --prefix=/usr/local
sudo ninja -C build install
```