/// <reference path="synchronized/events.ts" />


namespace Router {
    class Navigator {
        private readonly navigateCallbacks: Set<() => void> = new Set<() => void>();
        private readonly navigatorBarLoaded: synchronized.Event = new synchronized.Event();
        private readonly trailingSlash: RegExp = new RegExp(/^\/*/);

        private currentPath: string = location.pathname;

        public constructor() {
            $(
                () => {
                    this.initializePage();
                    $.get("/commons.html")
                        .done(
                            (e) => {
                                $("body").prepend(e);
                                this.navigatorBarLoaded.set();
                            }
                        );
                },
            );

            this.onNavigate(() => this.initializePage());
            addEventListener("popstate", () => this.navigate(location.pathname, false));
        }

        private initializePage(): void {
            const header = $("#header");
            if (header.length > 0) {
                document.title = header.text();
            }

            $(".navigate-commands").on("click", () => this.navigate("commands", true));
        }

        public waitForNavigatorBar(): Promise<void> {
            return this.navigatorBarLoaded.wait();
        }

        public onNavigate(callback: () => void): void {
            this.navigateCallbacks.add(callback);
        }

        public navigate(target: string, pushState: boolean): void {
            target = target.replace(this.trailingSlash, "");

            console.log(`Navigating from ${this.currentPath} to /${target}`);
            if (this.currentPath != target) {
                this.currentPath = "/" + target;
                const main = $("#main-content");
                main.empty();
                main.append(
                    $(
                        "<div>",
                        {
                            "class": "circular-progress-indicator",
                            "style": "position: absolute; left: 50%; top: 50%",
                        },
                    ),
                );
                main.load(
                    `/${target} #main-content`,
                    () => {
                        console.log(`Pushing /${target}`);
                        if (pushState) {
                            window.history.pushState(null, "", `/${target}`);
                        }

                        this.navigateCallbacks.forEach((func) => func());
                    },
                );
            }
        }
    }

    export const navigator: Navigator = new Navigator();
}


