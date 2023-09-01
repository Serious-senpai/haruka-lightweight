/// <reference path="router.ts" />


const urlPattern = new RegExp(/^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/);


function proxyView(): void {
    const $input = $("input#proxy-url-input");
    if ($input.length > 0) {
        $input.off().on("keydown", (e) => {
            if (e.key === "Enter") {
                const url = $input.val();
                if (typeof url === "string") {
                    url.trim();
                    if (url.match(urlPattern)) {
                        const proxyUrl = new URL(url);
                        proxyUrl.protocol = location.protocol;
                        proxyUrl.hostname += "." + location.hostname;
                        proxyUrl.port = location.port;
                        open(proxyUrl);

                    } else {
                        alert("Invalid URL scheme!");
                    }
                }
            }
        });
    }
}


router.navigator.onNavigate(() => proxyView());
$(() => proxyView());
