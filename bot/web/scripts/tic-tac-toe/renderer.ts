/// <reference path="rooms.ts" />
/// <reference path="../router.ts" />
/// <reference path="../utils.ts" />


namespace tic_tac_toe {
    class Renderer {
        private _room: Room | null = null;
        private readonly roomUrlPattern = new RegExp(/^\/tic-tac-toe\/room\/([\w\-\.~]+)\/?$/);

        public constructor() {
            console.log("Matching URL against room pattern", this.roomUrlPattern);
            const match = location.pathname.match(this.roomUrlPattern);
            if (match !== null) {
                const id = match[1];
                console.log(`URL matched with room ID ${id}`);
                Room.join(id).then((room) => this.room = room);
            }

            router.navigator.onNavigate(
                () => {
                    if (this._room !== null) {
                        Renderer.renderCallback(this._room);
                    }
                },
            );
        }

        /**
         * Navigate to the specified room by pushing it into the history stack.
         * @param room The room to navigate to
         */
        public navigate(room: Room): void {
            console.log(`Navigating to room ${room.id}`);
            router.navigator.navigate(
                `/tic-tac-toe/room/${room.id}`,
                true,
                () => {
                    Renderer.renderCallback(room);
                    this.room = room;
                },
            );
        }

        public get room(): Room | null {
            return this._room;
        }

        public set room(room: Room | null) {
            console.log("Setting renderer.room:", room);
            if (this._room !== null) {
                this._room.controller = null;
                this._room.removeCallback(Renderer.renderCallback);
            }

            if (room !== null) {
                if (room.controller === null) {
                    console.warn(`Renderer._room is set to room ${room.id}, but the websocket controller is null:`, room);
                }

                room.addCallback(Renderer.renderCallback);
            }

            this._room = room;
        }

        private static renderCallback(room: Room): void {
            console.log(`Rendering room ${room.id}`);
            const $infoColumn = $("div#tic-tac-toe-info-column");
            if ($infoColumn.length > 0) {
                console.log("Found matching element: ", $infoColumn);
                $infoColumn.children("div#tic-tac-toe-info-column-host").empty().append(
                    $("<img>", { "class": "account-avatar inline-icon", "src": room.host.user?.avatar.url ?? "/favicon.ico" }),
                    $(
                        "<span>",
                        {
                            "style": concatCSSStyles(
                                {
                                    "color": room.turn === 0 ? "yellow" : "white",
                                    "text-decoration": (room.ended && room.winner == 1) ? "line-through" : undefined,
                                },
                            )
                        },
                    )
                        .text(room.host.user?.name ?? "Guest"),
                );

                const $other = $infoColumn.children("div#tic-tac-toe-info-column-other").empty();
                if (room.other !== null) {
                    $other.append(
                        $("<img>", { "class": "account-avatar inline-icon", "src": room.other.user?.avatar.url ?? "/favicon.ico" }),
                        $(
                            "<span>",
                            {
                                "style": concatCSSStyles(
                                    {
                                        "color": room.turn === 1 ? "yellow" : "white",
                                        "text-decoration": (room.ended && room.winner == 0) ? "line-through" : undefined,
                                    },
                                )
                            },
                        )
                            .text(room.other.user?.name ?? "Guest"),
                    );
                } else {
                    $other.append($("<span>").text("Waiting for player..."));
                }

                $infoColumn.children("div#tic-tac-toe-info-column-logs").empty().html(room.logs.map(escapeHtml).join("<br>"));

                const $chat = $infoColumn.children("input#tic-tac-toe-info-column-chat").off();
                $chat.on("keydown", (e) => {
                    if (e.key === "Enter") {
                        const message = $chat.val() as string;
                        $chat.val("");

                        if (message === "/start") {
                            room.start();
                        } else {
                            room.chat(message);
                        }
                    }
                });

                const $board = $("table#tic-tac-toe-board-impl").children("tbody").empty();
                for (var row = 0; row < room.board.length; row++) {
                    const $row = $("<tr>");
                    for (var column = 0; column < room.board[row].length; column++) {
                        const block = room.board[row][column];
                        const r = row, c = column; // row and column are in the parent scope
                        const $block = $("<td>").on("click", () => room.move(r, c));
                        if (block !== null) {
                            $block.append(
                                $("<span>", { "class": "material-icons-outlined" })
                                    .text(block === 1 ? "close" : "circle"),
                            );
                        }

                        $row.append($block);
                    }

                    $board.append($row);
                }
            } else {
                console.log("No matching HTML element found, stopping rendering room.");
                renderer.room = null;
            }
        }
    }

    export const renderer = new Renderer();
    export function renderRooms(): void {
        console.log("Rendering rooms list");
        const $table = $("#tic-tac-toe-rooms");
        if ($table.length > 0) {
            console.log("Found matching element:", $table);
            $table.empty();
            $table.append(
                $("<tr>")
                    .append($("<th>", { "style": "width: 80%" }).text("Players"))
                    .append($("<th>", { "style": "width: 20%" }).text("Started")),
            );

            Room.rooms.forEach(
                (room) => {
                    $table.append(
                        $("<tr>", { "class": "cosplay-a" })
                            .append($("<td>").text(`${room.host.displayName} vs ${room.other?.displayName ?? "---"}`))
                            .append($("<td>").text(room.started ? "Yes" : "No"))
                            .on("click", () => room.join().then(() => renderer.navigate(room))),
                    );
                }
            );
        }
    }
}