import type { Plugin, ViteDevServer } from "vite";
import type { IncomingMessage, ServerResponse } from "http";
import { spawn, ChildProcess } from "child_process";
import path from "path";
import fs from "fs";

const PROJECT_ROOT = path.resolve(__dirname, "..", "..", "..");
const DATA_DIR = path.join(PROJECT_ROOT, "data");

let agentProcess: ChildProcess | null = null;

function readJSON(file: string): string | undefined {
  const p = path.join(DATA_DIR, file);
  if (!fs.existsSync(p)) return undefined;
  return fs.readFileSync(p, "utf-8");
}

function writeJSON(file: string, data: unknown): void {
  const p = path.join(DATA_DIR, file);
  fs.writeFileSync(p, JSON.stringify(data, null, 2), "utf-8");
}

function serveData(req: IncomingMessage, res: ServerResponse): boolean {
  const url = new URL(req.url || "/", "http://localhost");
  if (!url.pathname.startsWith("/data/")) return false;

  const relative = url.pathname.replace("/data/", "");
  // 安全检查
  if (relative.includes("..")) {
    res.statusCode = 403;
    res.end("Forbidden");
    return true;
  }

  const content = readJSON(relative);
  if (content !== undefined) {
    res.setHeader("Content-Type", "application/json");
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.end(content);
  } else {
    res.statusCode = 404;
    res.end("Not Found");
  }
  return true;
}

export function scanPlugin(): Plugin {
  return {
    name: "tablescope-scan-plugin",
    configureServer(server: ViteDevServer) {
      // Data 文件写入
      server.middlewares.use("/api/data/write", (req, res) => {
        if (req.method !== "POST") {
          res.statusCode = 405;
          res.end("Method Not Allowed");
          return;
        }
        let body = "";
        req.on("data", (chunk: Buffer) => {
          body += chunk.toString();
        });
        req.on("end", () => {
          try {
            const { file, data } = JSON.parse(body);
            writeJSON(file, data);
            res.setHeader("Content-Type", "application/json");
            res.end(JSON.stringify({ ok: true }));
          } catch (e: any) {
            res.statusCode = 400;
            res.setHeader("Content-Type", "application/json");
            res.end(JSON.stringify({ error: e.message }));
          }
        });
      });

      // Data 文件读取 — 必须是最后一个 middleware 兜底
      server.middlewares.use((req, res, next) => {
        if (serveData(req, res)) return;
        next();
      });

      // 启动扫描
      server.middlewares.use("/api/scan/start", (req, res) => {
        if (req.method !== "POST") {
          res.statusCode = 405;
          res.end("Method Not Allowed");
          return;
        }

        if (agentProcess) {
          res.statusCode = 409;
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ error: "扫描已在运行中" }));
          return;
        }

        let body = "";
        req.on("data", (chunk: Buffer) => {
          body += chunk.toString();
        });
        req.on("end", () => {
          let params: Record<string, string> = {};
          try {
            params = JSON.parse(body);
          } catch {
            // ignore
          }

          const dbId = params.db || "";
          const strategy = params.strategy || "";
          const root = path.resolve(__dirname, "..", "..", "..");

          // 读取配置
          const configPath = path.join(root, "data", "scan_config.json");
          let wsPort = "8765";
          let agentCommand = "python scan.py";
          if (fs.existsSync(configPath)) {
            const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
            wsPort = String(config.ws_port || 8765);
            agentCommand = config.agent_command || agentCommand;
          }

          const args = agentCommand.split(" ").slice(1);
          args.push("--db", dbId);
          args.push("--ws-port", wsPort);
          if (strategy) {
            args.push("--strategy", strategy);
          }

          const cmd = agentCommand.split(" ")[0];

          agentProcess = spawn(cmd, args, {
            cwd: root,
            shell: true,
            stdio: ["ignore", "pipe", "pipe"],
          });

          agentProcess.stdout?.on("data", (data: Buffer) => {
            console.log(`[agent] ${data.toString().trim()}`);
          });
          agentProcess.stderr?.on("data", (data: Buffer) => {
            console.error(`[agent] ${data.toString().trim()}`);
          });
          agentProcess.on("close", (code: number | null) => {
            console.log(`[agent] 进程退出, 退出码: ${code}`);
            agentProcess = null;
          });
          agentProcess.on("error", (err: Error) => {
            console.error(`[agent] 启动失败: ${err.message}`);
            agentProcess = null;
          });

          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ status: "started", ws_port: parseInt(wsPort) }));
        });
      });

      // 停止扫描
      server.middlewares.use("/api/scan/stop", (req, res) => {
        if (req.method !== "POST") {
          res.statusCode = 405;
          res.end("Method Not Allowed");
          return;
        }

        if (agentProcess) {
          agentProcess.kill("SIGTERM");
          agentProcess = null;
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ status: "stopped" }));
        } else {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ status: "not_running" }));
        }
      });

      // 检查 agent 状态
      server.middlewares.use("/api/scan/status", (_req, res) => {
        res.setHeader("Content-Type", "application/json");
        res.end(
          JSON.stringify({
            running: agentProcess !== null,
            pid: agentProcess?.pid || null,
          })
        );
      });
    },
  };
}
