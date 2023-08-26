/// <reference path="../client/http.ts" />


namespace discord {
    export class Command {
        private static readonly categoryParser: RegExp = new RegExp(/(.+?)\.\w+/);

        public readonly name: string;
        public readonly aliases: Array<string>;
        public readonly category: string;
        public readonly description: string;
        public readonly usage: string;

        private constructor(name: string, aliases: Array<string>, brief: string, description: string, usage: string) {
            this.name = name;
            this.aliases = aliases;
            this.category = brief.match(Command.categoryParser)![1];
            this.description = description;
            this.usage = usage;
        }

        private static fromObject(data: object): Command {
            return new Command(data["name"], data["aliases"], data["brief"], data["description"], data["usage"]);
        }

        public static updateCommands(callback: (commands: Array<Command>) => void): void {
            client.http.get("/api/commands")
                .done(
                    (data: Array<object>) => {
                        const commands: Array<Command> = new Array<Command>();
                        data.forEach((e) => commands.push(this.fromObject(e)));
                        callback(commands);
                    }
                );
        }
    }
}