/// <reference path="authorization.ts" />


namespace client {
    export class HTTPException extends Error { }

    class HTTP {
        public get<TContext = any>(url: string, settings?: JQuery.Ajax.AjaxSettingsBase<TContext>): JQuery.jqXHR<any> {
            var target: JQuery.UrlAjaxSettings<TContext> = {
                "url": url,
                "headers": authorization.header,
            };
            if (settings !== undefined) {
                Object.keys(settings).forEach(
                    (key) => {
                        if (key !== "url" && key !== "headers") {
                            target[key] = settings[key];
                        }
                    }
                );
            }

            return $.get(target);
        }
    }

    export const http = new HTTP();
}