if (typeof browser === "undefined") {
    var browser = chrome;
}

browser.runtime.onMessage.addListener(function (request, _, __) {
    browser.runtime.sendNativeMessage(
        "com.github.essmehdi.flow", {
            "url": request.url,
            "headers": []
        }
    );
});

browser.webRequest.onHeadersReceived.addListener(function (details) {
    console.log(details);
    if (details.type !== 'main_frame' && details.type !== 'sub_frame') return;
    const headers = details.responseHeaders;
    if (headers.find(header => header.name.toLowerCase() === 'content-disposition' && !header.value.startsWith("inline"))) {
        browser.storage.local.get(details.requestId).then(item => {
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