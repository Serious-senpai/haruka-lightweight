/// <reference path="client/http.ts" />


namespace Router {
    class Navigator {
        private readonly navigateCallbacks: Set<() => void> = new Set<() => void>();
        private readonly trailingSlash: RegExp = new RegExp(/^\/*/);

        private currentPath: string = location.pathname;

        public constructor() {
            $(() => this.initializePage());

            this.onNavigate(() => this.initializePage());
            addEventListener("popstate", () => this.navigate(location.pathname, false));
        }

        private initializePage(): void {
            const header = $("#header");
            if (header.length > 0) {
                document.title = header.text();
            }

            $(".navigate-commands").off().on("click", () => this.navigate("commands", true));
            $(".navigate-proxy").off().on("click", () => this.navigate("proxy", true));
        }

        public onNavigate(callback: () => void): void {
            this.navigateCallbacks.add(callback);
        }

        public navigate(target: string, pushState: boolean): void {
            target = target.replace(this.trailingSlash, "");

            console.log(`Navigating from ${this.currentPath} to /${target}`);
            if (this.currentPath != target) {
                this.currentPath = "/" + target;
                const $page = $("#page-view");
                $page.empty();
                $page.append(
                    $(
                        "<div>",
                        {
                            "class": "circular-progress-indicator",
                            "style": "position: absolute; left: 50%; top: 50%",
                        },
                    ),
                );

                client.http.get(`/${target}`).done(
                    (html: string) => {
                        const $dummy = $("<div>");
                        $dummy.html(html);
                        $page.html($dummy.find("div#page-view").html());

                        if (pushState) {
                            window.history.pushState(null, "", `/${target}`);
                        }

                        this.navigateCallbacks.forEach((func) => func());
                    }
                );
            }
        }
    }

    export const navigator: Navigator = new Navigator();
}
