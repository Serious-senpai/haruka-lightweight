/// <reference path="../client/authorization.ts" />


namespace tic_tac_toe {
    export function openWebSocket(path: string): Promise<WebSocket> {
        return new Promise<WebSocket>(
            (resolver) => {
                client.authorization.waitForInitialLogin().then(
                    () => {
                        const target = new URL(window.location.toString());
                        target.pathname = path;
                        target.protocol = target.protocol.replace("http", "ws");

                        const ws = new WebSocket(target);
                        ws.onopen = () => {
                            // Send authorization message
                            const token = client.authorization.token;
                            if (token !== null) {
                                ws.send(token);
                            } else {
                                ws.send("");
                            }

                            resolver(ws);
                        };
                    }
                );
            }
        );
    }
}