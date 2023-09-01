/// <reference path="client/http.ts" />


namespace router {
    class Navigator {
        private readonly navigateCallbacks: Set<() => void> = new Set<() => void>();
        private readonly trailingSlash: RegExp = new RegExp(/^\/*/);

        private currentPath: string = location.pathname;

        public constructor() {
            this.onNavigate(() => this.initializePage());
            addEventListener("popstate", () => this.navigate(location.pathname, false));
            $(() => this.initializePage());
        }

        private initializePage(): void {
            const header = $("#header");
            if (header.length > 0) {
                document.title = header.text();
            }

            $(".navigate-commands").off().on("click", () => this.navigate("commands", true));
            $(".navigate-proxy").off().on("click", () => this.navigate("proxy", true));
            $(".navigate-tic-tac-toe").off().on("click", () => this.navigate("tic-tac-toe", true));
        }

        public onNavigate(callback: () => void): void {
            console.log("Adding a callback to navigator.onNavigate:", callback);
            this.navigateCallbacks.add(callback);
        }

        public navigate(target: string, pushState: boolean, whenLoaded?: () => void): void {
            target = target.replace(this.trailingSlash, "");

            console.log(`Navigating from ${this.currentPath} to /${target}`);
            if (this.currentPath !== target) {
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

                $page.load(
                    `/${target} #page-view-ajax-load`,
                    () => {
                        console.log(`Finished loading HTML content from /${target}`);
                        if (pushState) {
                            window.history.pushState(null, "", `/${target}`);
                        }

                        this.navigateCallbacks.forEach((func) => func());
                        if (whenLoaded !== undefined) whenLoaded();
                    }
                );
            }
        }
    }

    export const navigator: Navigator = new Navigator();
}
