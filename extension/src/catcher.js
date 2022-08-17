if (typeof browser === "undefined") {
    var browser = chrome;
}

const extensionsBlacklist = [
    "html", "png", "jpg", "jpeg", "gif", "aspx", "php"
]

// Context menu to force a download
browser.menus.create({
    id: "download-flow",
    title: "Download with Flow",
    contexts: ["link"]
});

// Context menu item clicked
browser.menus.onClicked.addListener(function(info, tab) {
    if (info.menuItemId === "download-flow") {
        browser.runtime.sendNativeMessage(
            "com.github.essmehdi.flow", {
                "url": info.linkUrl,
                "headers": []
            }
        );
    }
});

function getFileDetailsDisposition(header) {
    const match = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(header);
    if (match && match[1]) {
        const filename = match[1].trim();
        const dotIndex = filename.lastIndexOf('.');
        console.log(filename, dotIndex);
        return {
            filename,
            extension: dotIndex > -1 ? filename.substring(dotIndex + 1) : ""
        }
    }
}

function getFileDetailsURL(url) {
    const parsed = new URL(url);
    const split = parsed.pathname.split('/');
    const lastPath = split[split.length - 1];
    const filename = lastPath || parsed.hostname;
    const dotIndex = lastPath.lastIndexOf('.');
    return {
        filename,
        extension: dotIndex > -1 ? filename.substring(dotIndex + 1) : ""
    };
    
}

function shouldCatch(details) {
    const headers = details.responseHeaders;
    const dispositionHeader = headers.find(header => header.name.toLowerCase() === 'content-disposition' && !header.value.startsWith("inline"));
    
    // Get file details from response
    const filedetails = dispositionHeader ? getFileDetailsDisposition(dispositionHeader.value) : getFileDetailsURL(details.url);

    // Download if there is 'Content-Disposition' or (file has an extension and not an browser openable file)
    return dispositionHeader || 
            (filedetails.extension 
            && !extensionsBlacklist.includes(filedetails.extension)
            && !headers.find(header => 
                    header.name.toLowerCase() === 'content-type' && header.value.includes('text/html')
                )
            )
}

browser.webRequest.onHeadersReceived.addListener(function (details) {
    if (details.type !== 'main_frame' && details.type !== 'sub_frame') return;
    if (shouldCatch(details)) {
        browser.storage.local.get(details.requestId, function(item) {
            browser.runtime.sendNativeMessage(
                "com.github.essmehdi.flow", {
                    "url": details.url,
                    "headers": item[details.requestId]
                }
            );
        });
        browser.storage.local.remove(details.requestId);
        return { cancel: true };
    }
}, { urls: ['<all_urls>'] }, ['responseHeaders', 'blocking']);

browser.webRequest.onSendHeaders.addListener(function (details) {
    browser.storage.local.set(
        { [details.requestId]: details.requestHeaders }
    );
}, { urls: ["<all_urls>"] }, ['requestHeaders']);

browser.webRequest.onCompleted.addListener(function (details) {
    browser.storage.local.remove(details.requestId);
}, { urls: ["<all_urls>"] }, ['responseHeaders']);

browser.webRequest.onErrorOccurred.addListener(function (details) {
    browser.storage.local.remove(details.requestId);
}, { urls: ["<all_urls>"] });
