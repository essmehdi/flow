document.querySelectorAll("a").forEach(link => link.addEventListener("click", event => {
    console.log("Clicked");
    const clickedLink = event.target;
    const download = clickedLink.getAttribute("download");
    if (download !== null) {
        event.preventDefault();
        const url = clickedLink.getAttribute("href");
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