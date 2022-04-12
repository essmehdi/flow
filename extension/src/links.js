document.querySelectorAll("a").forEach(link => link.addEventListener("click", event => {
    console.log("Clicked");
    if (link.hasAttribute("download")) {
        event.preventDefault();
        const url = link.getAttribute("href");
        var final = url;
        try {
            new URL(final);
        } catch {
            final = window.location.origin + url;
            try {
                new URL(final);
            } catch {
                return;   
            }
        }
        console.log(final);
        browser.runtime.sendMessage({ url: final });
    }
}));