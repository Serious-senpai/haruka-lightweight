/// <reference path="router.ts" />
/// <reference path="client/authorization.ts" />
/// <reference path="discord/commands.ts" />


function updateCommands(): void {
    const $container = $("div#commands");
    if ($container.length > 0) {
        const $hiddenModals = $("div#hidden-modals");
        discord.Command.updateCommands(
            (commands) => {
                if ($container.length > 0) {
                    const categoryToCommands: Map<string, Array<discord.Command>> = new Map<string, Array<discord.Command>>();
                    for (var command of commands) {
                        var array = categoryToCommands.get(command.category);
                        if (array === undefined) {
                            array = new Array<discord.Command>();
                            categoryToCommands.set(command.category, array);
                        }

                        array.push(command);
                    }

                    $container.empty();
                    $hiddenModals.empty();
                    categoryToCommands.forEach(
                        (commands, category) => {
                            commands.sort((first, second) => first.name.localeCompare(second.name));
                            const $commands = commands.map(
                                (command) => $(
                                    "<div>",
                                    {
                                        "style": concatCSSStyles(
                                            {
                                                "border-radius": "5px",
                                                "border-style": "solid",
                                                "box-sizing": "border-box",
                                                "margin": "10px",
                                                "padding": "10px",
                                                "width": "100%",
                                            },
                                        ),
                                    },
                                ).append(
                                    $("<h3>", { "style": "color: red; margin: 0" }).text(command.name),
                                    $("<i>").html(escapeHtml(command.usage).replace("\n", "<br>")),
                                    $("<p>", { "style": "color: yellow;" }).html(escapeHtml(command.description).replace("\n", "<br>")),
                                ),
                            );
                            const $searchInput = $(
                                "<input>",
                                {
                                    "autocomplete": "off",
                                    "autofocus": "true",
                                    "placeholder": "Search for commands",
                                    "style": "width: 70%",
                                }
                            ).on(
                                "input",
                                () => {
                                    const search = $searchInput.val() ?? "";
                                    if (typeof search === "string") {
                                        $commands.forEach(
                                            (element) => {
                                                if (element.children("h3").text().includes(search)) {
                                                    element.show();
                                                } else {
                                                    element.hide();
                                                }
                                            },
                                        );
                                    }
                                }
                            );

                            const $modalContainer = $(
                                "<div>",
                                {
                                    "class": "container",
                                    "style": concatCSSStyles(
                                        {
                                            "border-color": "blue",
                                            "color": "yellow",
                                            "padding-left": "30px",
                                            "padding-right": "30px",
                                            "padding-top": "20px",
                                        },
                                    ),
                                }
                            ).append(
                                $(
                                    "<div>",
                                    {
                                        "class": "close-button cosplay-a",
                                    },
                                ).append(
                                    $("<span>", { "class": "material-icons" }).text("close"),
                                ).on("click", () => $modal.hide()),
                                $searchInput,
                                $commands,
                            );

                            const $modal = $("<div>", { "class": "modal" })
                                .append($modalContainer)
                                .on(
                                    "click",
                                    (e) => {
                                        if (!$modalContainer.is(e.target) && $modalContainer.has(e.target).length == 0) {
                                            $modal.hide();
                                        }
                                    },
                                );

                            $container.append(
                                $(
                                    "<div>",
                                    {
                                        "class": "cosplay-a",
                                        "style": concatCSSStyles(
                                            {
                                                "border-color": "blue",
                                                "border-radius": "15px",
                                                "border-style": "solid",
                                                "box-sizing": "border-box",
                                                "color": "aqua",
                                                "margin": "5px",
                                                "padding-left": "10px",
                                                "padding-right": "10px",
                                                "width": "80%",
                                            },
                                        ),
                                    },
                                ).append(
                                    $("<h4>", { "style": "color: red" }).text(captialize(category)),
                                    $("<p>", { "style": "color: yellow" }).text(commands.map((command) => command.name).join(", ")),
                                ).on(
                                    "click",
                                    () => $modal.show(),
                                ),
                            );

                            $hiddenModals.append($modal);
                        },
                    );
                }
            },
        );
    }
}


client.authorization.onLogin(() => updateCommands());
Router.navigator.onNavigate(() => updateCommands());
updateCommands();
