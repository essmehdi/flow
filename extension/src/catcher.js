if (typeof browser === "undefined") {
    var browser = chrome;
}

let requests = [];

browser.runtime.onMessage.addListener(function (request, _, __) {
    browser.runtime.sendNativeMessage(
        "com.github.essmehdi.atay", {
            "url": request.url,
            "headers": []
        }
    );
});

browser.webRequest.onHeadersReceived.addListener(function (details) {
    if (details.type !== 'main_frame' && details.type !== 'sub_frame') return;
    const headers = details.responseHeaders;
    if (headers.find(header => header.name === 'content-disposition')) {
        browser.storage.local.get(details.requestId).then(item => {
            browser.runtime.sendNativeMessage(
                "com.github.essmehdi.atay", {
                    "url": details.url,
                    "headers": item[details.requestId]
                }
            );
        });
        browser.storage.local.remove(details.requestId);
        return { cancel: true };
    }
}, { urls: ['<all_urls>'] }, ['responseHeaders', 'blocking']);

/*const removeRequestByID = id => {
    index = requests.findIndex(request => request.requestId == id);
    toDelete = requests[index];
    if (index != -1) {
        requests.splice(index, 1);
        return toDelete;
    }
}

const removeRequestByURL = url => {
    index = requests.findIndex(request => request.url === url);
    toDelete = requests[index];
    if (index != -1) {
        requests.splice(index, 1);
        return toDelete;
    }
}

const getRequest = id => {
    return requests.find(request => request.requestId === id);
}*/

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

/*browser.downloads.onCreated.addListener(item => {
    const url = item.finalUrl || item.url;
    if (item.state === "in_progress") {
        const request = removeRequestByURL(url);
        if (!request) {
            return;
        }
        browser.downloads.cancel(item.id);
        browser.downloads.erase({ id: item.id });
        browser.runtime.sendNativeMessage("com.github.essmehdi.atay", { "url": url, "headers": request.requestHeaders });
    }
});*/
