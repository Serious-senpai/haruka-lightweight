/// <reference path="../discord/users.ts" />
/// <reference path="../synchronized/events.ts" />


namespace client {
    class Authorization {
        private static readonly EVENT_LOGIN: string = "haruka.login";
        private static readonly EVENT_LOGOUT: string = "haruka.logout";
        private static readonly LOCAL_STORAGE_TOKEN_KEY: string = "haruka.authorizationToken";

        private _user: discord.User | null = null;
        private _token: string | null = null;
        private _callbacks: Set<(user: discord.User | null) => void> = new Set<(user: discord.User | null) => void>();
        private $_accountZone: JQuery<HTMLElement> | null = null;
        private $_loginModal: JQuery<HTMLElement> | null = null;
        private $_loginKeyInput: JQuery<HTMLElement> | null = null;

        private readonly initialLogin: synchronized.Event = new synchronized.Event();
        private readonly navigatorBarLoaded: synchronized.Event = new synchronized.Event();

        public constructor() {
            $(
                () => {
                    $.get("/commons.html")
                        .done(
                            (e) => {
                                $("body").prepend(e);
                                this.navigatorBarLoaded.set();
                            }
                        );
                },
            );
            this.waitForNavigatorBar().then(
                () => {
                    /* Login using token from localStorage */
                    const token = localStorage[Authorization.LOCAL_STORAGE_TOKEN_KEY];
                    this.update(null, null);  // trigger element creation
                    if (typeof token === "string") {
                        $.get(
                            {
                                "url": "/api/login",
                                "headers": { "X-Auth-Token": token },
                            },
                        ).done(
                            (data: object) => {
                                if (data["success"]) {
                                    this.update(discord.User.fromObject(data["user"]), token);
                                }

                                this.initialLogin.set();
                            }
                        );
                    } else {
                        this.initialLogin.set();
                    }

                    /* Add listeners for login/logout events.
                    These listeners need to be added only once since the navigator bar and login modal
                    persists across page navigations */
                    this.$accountZone.on(Authorization.EVENT_LOGIN, () => this.login())
                        .on(Authorization.EVENT_LOGOUT, () => this.logout());

                    this.$loginKeyInput.on("keydown", (e) => {
                        if (e.key === "Enter") {
                            this.submitKey();
                        }
                    });

                    this.$loginModal.find(".close-button").on("click", () => this.$loginModal.show());
                }
            );
        }

        public waitForInitialLogin(): Promise<void> {
            return this.initialLogin.wait();
        }

        public waitForNavigatorBar(): Promise<void> {
            return this.navigatorBarLoaded.wait();
        }

        private get $accountZone(): JQuery<HTMLElement> {
            this.$_accountZone ??= $("#account-zone");
            return this.$_accountZone;
        }

        private get $loginModal(): JQuery<HTMLElement> {
            this.$_loginModal ??= $("#login-modal");

            // https://stackoverflow.com/a/7385673
            const $modal = this.$_loginModal,
                $container = this.$_loginModal.find(".container");
            $modal.on(
                "click",
                (e) => {
                    if (!$container.is(e.target) && $container.has(e.target).length === 0) {
                        $modal.hide();
                    }
                }
            );

            return this.$_loginModal;
        }

        private get $loginKeyInput(): JQuery<HTMLElement> {
            this.$_loginKeyInput ??= $("input#login-key");
            return this.$_loginKeyInput;
        }

        public get user(): discord.User | null {
            return this._user;
        }

        public get token(): string | null {
            return this._token;
        }

        public get header(): JQuery.PlainObject<string | null | undefined> {
            if (this._token === null) return {};
            return { "X-Auth-Token": this._token };
        }

        public onAuthorizationUpdate(callback: (user: discord.User | null) => void): void {
            console.log("Adding a callback to authorization.onAuthorizationUpdate:", callback);
            this._callbacks.add(callback);
        }

        private update(user: discord.User | null, token: string | null): void {
            this._user = user;
            this._token = localStorage[Authorization.LOCAL_STORAGE_TOKEN_KEY] = token;

            this.$accountZone.empty();
            if (user === null) {
                this.$accountZone.append(
                    $("<div>", { "class": "change-bg-on-hover cosplay-a navigator-item expanded", "id": "login-button" }).append(
                        $("<span>", { "class": "material-icons-outlined inline-icon" }).html("login"),
                        $("<span>", { "class": "hide-when-collapsed" }).html("Login"),
                    ).on("click", () => this.$accountZone.trigger(Authorization.EVENT_LOGIN)),
                );
            } else {
                this.$accountZone.append(
                    $("<div>", { "id": "account-display" }).append(
                        $("<img>", { "class": "account-avatar inline-icon", "src": user.avatar.url }),
                        $("<span>", { "class": "hide-when-collapsed" }).html(user.name),
                    ),
                    $("<div>", { "class": "change-bg-on-hover cosplay-a navigator-item expanded", "id": "logout-button" }).append(
                        $("<span>", { "class": "material-icons-outlined inline-icon" }).html("logout"),
                        $("<span>", { "class": "hide-when-collapsed" }).html("Logout"),
                    ).on("click", () => this.$accountZone.trigger(Authorization.EVENT_LOGOUT)),
                );
            }

            this._callbacks.forEach((func) => func(user));
            console.log("User updated to:", user);
        }

        private login(): void {
            this.$loginModal.show();
        }

        private logout(): void {
            this.update(null, null);
        }

        public submitKey(): void {
            const key = this.$loginKeyInput.val() as string;
            this.$loginKeyInput.val("");
            this.$loginModal.hide();

            this.$accountZone.empty();
            this.$accountZone.append(
                $("<div>", { "class": "circular-progress-indicator" })
            );

            $.post({
                "url": "/api/login",
                "headers": { "Login-Key": key },
            }).done(
                (data: object) => {
                    if (data["success"]) {
                        this.update(discord.User.fromObject(data["user"]), data["token"]);
                    } else {
                        this.update(null, null);  // trigger element creation
                        alert("Invalid credentials");
                    }
                }
            );
        }
    }

    export const authorization = new Authorization();
}
