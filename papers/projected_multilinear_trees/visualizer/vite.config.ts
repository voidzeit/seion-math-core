import { writeFileSync } from "node:fs";
import { defineConfig, type Plugin } from "vite";

/**
 * Dev-only endpoint that lets the page report which GPU actually served it.
 *
 * `powerPreference: "high-performance"` is a hint a browser may ignore, and on
 * a laptop with switchable graphics it frequently does. Reading the adapter off
 * a screenshot or asking someone to eyeball a panel is not evidence, so the
 * page POSTs its telemetry here and the result is written to disk where it can
 * be diffed between launch configurations.
 */
function gpuReport(): Plugin {
  return {
    name: "pmt-gpu-report",
    apply: "serve",
    configureServer(server) {
      server.middlewares.use("/__gpu", (req, res) => {
        if (req.method !== "POST") {
          res.statusCode = 405;
          return res.end();
        }
        let body = "";
        req.on("data", (c) => (body += c));
        req.on("end", () => {
          try {
            const parsed = JSON.parse(body);
            writeFileSync(
              new URL("./gpu_report.json", import.meta.url),
              JSON.stringify({ at: new Date().toISOString(), ...parsed }, null, 2) + "\n",
            );
          } catch {
            /* a malformed report is not worth crashing the dev server over */
          }
          res.setHeader("content-type", "application/json");
          res.end('{"ok":true}');
        });
      });
    },
  };
}

export default defineConfig({ plugins: [gpuReport()] });
