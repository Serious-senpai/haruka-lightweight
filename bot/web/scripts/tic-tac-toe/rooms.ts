/// <reference path="players.ts" />
/// <reference path="websocket.ts" />
/// <reference path="../router.ts" />
/// <reference path="../utils.ts" />
/// <reference path="../client/http.ts" />
/// <reference path="../collections/pair.ts" />


namespace tic_tac_toe {
    export const BOARD_SIZE: number = 15;

    /**
     * Represents a tic-tac-toe room, which consists of 2 players and any number of spectators.
     */
    export class Room {
        /** The room ID */
        public readonly id: string;

        /** The room logs for chat messages and events */
        public readonly logs: Array<string>;
        private _host: Player;
        private _other: Player | null;

        /** The tic-tac-toe board */
        public readonly board: Array<Array<number | null>>;
        private _turn: number;
        private _started: boolean;
        private _ended: boolean;
        private _winner: number;

        // State management
        private _controller: WebSocket | null = null;
        private readonly _updateCallbacks: Set<(room: Room) => void> = new Set<(room: Room) => void>();

        private constructor(
            id: string,
            logs: Array<string>,
            host: Player,
            other: Player | null,
            board: Array<Array<number | null>>,
            turn: number,
            started: boolean,
            ended: boolean,
            winner: number,
        ) {
            console.log(`Constructing room ${id}`);
            this.id = id;
            this.logs = logs;
            this._host = host;
            this._other = other;
            this.board = board;
            this._turn = turn;
            this._started = started;
            this._ended = ended;
            this._winner = winner;
        }

        /** The room host */
        public get host(): Player {
            return this._host;
        }

        /** The host's opponent */
        public get other(): Player | null {
            return this._other;
        }

        /**
         * Indicates the current turn of the game.
         * It is important to {@link started check whether the game was started} first.
         * 
         * 0 -> host's turn
         * 
         * 1 -> opponent's turn
         */
        public get turn(): number {
            return this._turn;
        }

        /** Whether the game was started */
        public get started(): boolean {
            return this._started;
        }

        public get ended(): boolean {
            return this._ended;
        }

        public get winner(): number {
            return this._winner;
        }

        /**
         * The {@link WebSocket} that perform user operations on this room.
         */
        public get controller(): WebSocket | null {
            return this._controller;
        }

        public set controller(websocket: WebSocket | null) {
            console.log(`Updating controller of room ${this.id}:`, websocket);
            if (this._controller !== null) {
                this._controller.close();
            }

            if (websocket !== null) {
                websocket.onmessage = (e) => {
                    const received = JSON.parse(e.data);
                    console.log(`Received websocket message for room ${this.id}:`, received);
                    if (received["error"]) {
                        alert(received["message"]);
                    } else {
                        /* Note that there will be 2 updates upon the arrival of new data. The first update is
                        due to the line below, and the second one is from the global websocket (the one connecting
                        to /api/tic-tac-toe/rooms).
                        This implementation seems redundant but it makes everything works correctly anyway. */
                        this.update(received["data"]);
                    }
                };
                websocket.onerror = null;
            }

            this._controller = websocket;
        }

        public async join(): Promise<Room> {
            const room = await Room.join(this.id);
            if (room !== this) {
                console.error("Calling room.join() returned a different instance:\n", this, room);
            }

            return room;
        }

        /** Send a websocket message to start the game */
        public start(): void {
            console.log(`Starting room ${this.id}`);
            if (this._controller !== null) {
                this._controller.send("START");
            } else {
                console.warn("Cannot start the game, controller is currently null");
            }
        }

        public chat(message: string): void {
            console.log(`Sending message in room ${this.id}: ${message}`);
            if (this._controller !== null) {
                this._controller.send(`CHAT ${message}`);
            } else {
                console.warn("Cannot send message, controller is currently null");
            }
        }

        public move(row: number, column: number): void {
            console.log(`Making a move in room ${this.id} at block (${row}, ${column})`);
            if (this._controller !== null) {
                this._controller.send(`MOVE ${row} ${column}`);
            } else {
                console.warn("Cannot make a move, controller is currently null");
            }
        }

        /**
         * Register a callback to be called each time this room has it state updated.
         * @param callback The callback function to register
         */
        public addCallback(callback: (room: Room) => void): void {
            console.log(`Registering callback for room ${this.id}:`, callback);
            this._updateCallbacks.add(callback);
        }

        /**
         * Remove a callback added by {@link addCallback}
         * @param callback The callback function to remove
         */
        public removeCallback(callback: (room: Room) => void): void {
            console.log(`Unregistering callback for room ${this.id}:`, callback);
            this._updateCallbacks.delete(callback);
        }

        public readonly blockUpdated: Array<Array<boolean>> = construct2DArray(BOARD_SIZE, BOARD_SIZE, false);

        private hasUpdate(newBoard: Array<Array<number | null>>): boolean {
            for (var i = 0; i < BOARD_SIZE; i++) {
                for (var j = 0; j < BOARD_SIZE; j++) {
                    if (this.board[i][j] !== newBoard[i][j]) return true;
                }
            }

            return false;
        }

        private update(data: object): void {
            console.log(`Updating state for room ${this.id}:`, data);
            if (data["id"] === this.id) {
                for (var i = this.logs.length; i < data["logs"].length; i++) {
                    this.logs.push(data["logs"][i]);
                }

                this._host = Player.fromObject(data["host"]);
                this._other = data["other"] !== null ? Player.fromObject(data["other"]) : null;

                if (this.hasUpdate(data["board"])) {
                    for (var i = 0; i < BOARD_SIZE; i++) {
                        for (var j = 0; j < BOARD_SIZE; j++) {
                            this.blockUpdated[i][j] = (this.board[i][j] !== data["board"][i][j]);
                        }
                    }
                }

                for (var i = 0; i < BOARD_SIZE; i++) {
                    for (var j = 0; j < BOARD_SIZE; j++) {
                        this.board[i][j] = data["board"][i][j];
                    }
                }

                this._turn = data["turn"];
                this._started = data["started"];
                this._ended = data["ended"];
                this._winner = data["winner"];

                this._updateCallbacks.forEach((func) => func(this));
            } else {
                console.warn("Invalid websocket controller for room:", this, "\nData received:", data);
            }
        }

        /**
         * Construct a {@link Room room} from the provided data.
         * If a room with the same ID already exists in the cache, update and return that room instead.
         * @param data The room data (provided by the server)
         * @returns The room created or fetched from the cache
         */
        public static fromObject(data: object): Room {
            console.log("Creating room from data", data);
            const id = data["id"];
            const cached = Room.cache.get(id);
            if (cached !== undefined) {
                console.log(`Found cached room with matching id:`, cached);
                cached.update(data);
                return cached;
            }

            const room = new Room(
                id,
                data["logs"],
                Player.fromObject(data["host"]),
                data["other"] !== null ? Player.fromObject(data["other"]) : null,
                data["board"],
                data["turn"],
                data["started"],
                data["ended"],
                data["winner"],
            );
            Room.cache.set(id, room);
            console.log("Added a room to the cache:", Room.cache);
            return room;
        }

        /**
         * Host a new room.
         * @returns The newly hosted room
         */
        public static async create(): Promise<Room> {
            console.log("Sending request to host a new room");
            const waiter = new Promise<Promise<Room>>(
                (resolver) => {
                    client.http.get("/api/tic-tac-toe/create", { "dataType": "json" }).done(
                        (data: object) => {
                            const id = data["id"] as string;
                            console.log(`Got vacant ID ${id}`);
                            resolver(this.join(id));
                        }
                    );
                }
            );

            return await waiter;
        }

        /**
         * Join a room with the given ID.
         * @param id The room ID to join
         * @returns The joined room
         */
        public static async join(id: string): Promise<Room> {
            console.log(`Joining room ${id}`);
            const cached = Room.cache.get(id);
            if (cached !== undefined && cached?._controller !== null) {
                console.log("Found cached room with active controller", cached, ". Joining...");
                return cached;
            }

            const waiter = new Promise<Room>(
                (resolver, rejecter) => {
                    openWebSocket(`/api/tic-tac-toe/room/${id}`).then(
                        (websocket) => {
                            websocket.onmessage = (e) => {
                                console.log(`Received message from /api/tic-tac-toe/room/${id}:`, e);
                                const received = JSON.parse(e.data);
                                if (received["error"]) {
                                    rejecter(received["message"]);
                                } else {
                                    const room = Room.fromObject(received["data"]); // still use the cached instance if possible
                                    room.controller = websocket;
                                    resolver(room);
                                }
                            };
                            websocket.onerror = (e) => rejecter(e);
                        }
                    );
                }
            );

            return await waiter;
        }

        // Rooms management
        private static _updateWebsocket: WebSocket | null = null;
        private static _rooms: Array<Room> | null = null;
        private static readonly cache: Map<string, Room> = new Map<string, Room>();
        private static readonly _callbacks: Set<(rooms: Array<Room>) => void> = new Set<(rooms: Array<Room>) => void>();

        /**
         * Register a callback to be called when the rooms list is updated. After registration is
         * completed, the callback is called immediately.
         * @param callback The callback to be called each time the rooms list is updated
         */
        public static register(callback: (rooms: Array<Room>) => void): void {
            console.log("Adding a rooms list listener:", callback);
            Room._callbacks.add(callback);
            if (Room._rooms === null) {
                Room.updateRooms();
            } else {
                callback(Room._rooms);
            }
        }

        /**
         * Unregister a callback registered by {@link register}
         * @param callback The callback to remove
         */
        public static unregister(callback: (rooms: Array<Room>) => void): void {
            console.log("Removing a rooms list listener:", callback);
            Room._callbacks.delete(callback);
        }

        public static get rooms(): Array<Room> {
            return Room._rooms ?? [];
        }

        private static updateRooms(): void {
            console.log("Opening a new websocket to stream rooms list state");
            openWebSocket("/api/tic-tac-toe/rooms").then(
                (websocket) => {
                    if (Room._updateWebsocket !== null) Room._updateWebsocket.close();
                    Room._updateWebsocket = websocket;

                    websocket.onmessage = (e) => {
                        const received = JSON.parse(e.data);
                        if (received["error"]) {
                            alert(received["message"]);
                        } else {
                            const rooms: Array<Room> = [];
                            for (var d of received["data"]) {
                                rooms.push(Room.fromObject(d));
                            }

                            Room._rooms = rooms;
                            Room._callbacks.forEach((func) => func(rooms));
                        }
                    };
                }
            );
        }
    }
}
