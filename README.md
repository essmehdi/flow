# Flow - The download manager for GNOME

![](screenshots/1.png)

A utility application to automatically organize and keep track of your downloads designed for GNOME. The project is still in early stage with basic functionalities of downloading and sorting. This is the main features task list:

- [x] Basic download (cURL)
- [x] Auto-sorting based on file extension
- [ ] Browser extension
- [ ] Resume a download with a new link
- [ ] Queues

## Browser extension

In this repository, there is a folder that contains the extension files. Currently, it is not bundled to be available in the extensions stores. You will have to manually enable it using your browser's developer mode when it is complete.

## Building & installing

To build from source, clone this repository and build the project with Meson:

```shell
git clone https://github.com/essmehdi/flow
cd flow
meson build --prefix=/usr/local
sudo ninja -C build install
```