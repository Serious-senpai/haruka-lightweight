/// <reference path="router.ts" />


function proxyPreview(): void {
    const $input = $("input#proxy-url-input");
    if ($input.length > 0) {
        $input.off().on("keydown", (e) => {
            if (e.key === "Enter") {
                const url = $input.val();
                if (typeof url === "string") {
                    url.trim();
                    if (url.startsWith("http")) {
                        const proxyUrl = new URL(url);
                        proxyUrl.protocol = location.protocol;
                        proxyUrl.hostname += "." + location.hostname;
                        proxyUrl.port = location.port;
                        console.log(proxyUrl.toString());
                        open(proxyUrl);

                    } else {
                        alert("Invalid URL scheme!");
                    }
                }
            }
        });
    }
}


Router.navigator.onNavigate(() => proxyPreview());
$(() => proxyPreview());
