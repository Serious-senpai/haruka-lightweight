/// <reference path="router.ts" />
/// <reference path="tic-tac-toe/rooms.ts" />
/// <reference path="tic-tac-toe/renderer.ts" />


function setUpRoomsView(): void {
    const $hostButton = $("#host-game-button");
    if ($hostButton.length > 0) {
        tic_tac_toe.renderRooms();
        $hostButton.off().on("click", () => tic_tac_toe.Room.create().then((room) => tic_tac_toe.renderer.navigate(room)));
    }
}


tic_tac_toe.Room.register(() => tic_tac_toe.renderRooms());
router.navigator.onNavigate(() => setUpRoomsView());
$(() => setUpRoomsView());
