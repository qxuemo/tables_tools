import { ref, reactive, watch, type Ref } from "vue";
import type {
  ConnectionInfo,
  ScanConfig,
  TableSchema,
  RelationInfo,
  ExtensionInfo,
} from "@/types";

const DATA_PREFIX = "/data";

// ── Connections ──────────────────────────────────────

export function useConnections() {
  const connections: Ref<ConnectionInfo[]> = ref([]);
  const selectedId: Ref<string | null> = ref(null);

  async function load() {
    try {
      const res = await fetch(`${DATA_PREFIX}/connections.json`);
      if (res.ok) {
        connections.value = await res.json();
      }
    } catch {
      // 文件不存在 = 无连接
    }
  }

  async function save(conn: ConnectionInfo) {
    const idx = connections.value.findIndex((c) => c.id === conn.id);
    if (idx >= 0) {
      connections.value[idx] = conn;
    } else {
      connections.value.push(conn);
    }
    await persistConnections();
  }

  async function remove(id: string) {
    connections.value = connections.value.filter((c) => c.id !== id);
    if (selectedId.value === id) selectedId.value = null;
    await persistConnections();
  }

  async function persistConnections() {
    // 通过 Vite API 写入 data 目录，或仅内存
    try {
      await fetch("/api/data/write", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file: "connections.json",
          data: connections.value,
        }),
      });
    } catch {
      console.warn("无法持久化连接配置");
    }
  }

  function select(id: string) {
    selectedId.value = id;
  }

  return { connections, selectedId, load, save, remove, select };
}

// ── Relations ────────────────────────────────────────

export function useRelations() {
  const schema: Ref<TableSchema | null> = ref(null);
  const relations: Ref<RelationInfo[]> = ref([]);
  const loading = ref(false);

  async function load(dbId: string) {
    loading.value = true;
    try {
      const [schemaRes, relRes] = await Promise.all([
        fetch(`${DATA_PREFIX}/${dbId}/schema.json`),
        fetch(`${DATA_PREFIX}/${dbId}/relations.json`),
      ]);
      if (schemaRes.ok) schema.value = await schemaRes.json();
      if (relRes.ok) relations.value = await relRes.json();
    } catch (e) {
      console.error("加载数据失败:", e);
    } finally {
      loading.value = false;
    }
  }

  function clear() {
    schema.value = null;
    relations.value = [];
  }

  return { schema, relations, loading, load, clear };
}

// ── WebSocket ────────────────────────────────────────

export function useWebSocket() {
  const ws = ref<WebSocket | null>(null);
  const status = ref<"connecting" | "connected" | "disconnected">("disconnected");
  const lastMessage = ref<any>(null);
  const progress = reactive({
    phase: "",
    currentTable: "",
    tablesDone: 0,
    tablesTotal: 0,
    candidatesFound: 0,
  });

  function connect(port: number) {
    disconnect();
    status.value = "connecting";
    const url = `ws://localhost:${port}`;
    const socket = new WebSocket(url);
    socket.onopen = () => {
      status.value = "connected";
    };
    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      lastMessage.value = msg;
      if (msg.type === "progress") {
        progress.phase = msg.phase || progress.phase;
        progress.currentTable = msg.current_table || "";
        progress.tablesDone = msg.tables_done || 0;
        progress.tablesTotal = msg.tables_total || 0;
        progress.candidatesFound = msg.candidates_found || 0;
      } else if (msg.type === "phase") {
        progress.phase = msg.phase || "";
      }
    };
    socket.onclose = () => {
      status.value = "disconnected";
    };
    socket.onerror = () => {
      status.value = "disconnected";
    };
    ws.value = socket;
  }

  function disconnect() {
    if (ws.value) {
      ws.value.close();
      ws.value = null;
    }
    status.value = "disconnected";
  }

  return { ws, status, lastMessage, progress, connect, disconnect };
}

// ── Scan ─────────────────────────────────────────────

export function useScan() {
  const scanning = ref(false);
  const agentStatus = ref<"offline" | "starting" | "scanning" | "analyzing" | "done" | "error">("offline");
  const error = ref("");

  async function startScan(
    dbId: string,
    strategy?: string,
    wsPort?: number,
  ) {
    scanning.value = true;
    agentStatus.value = "starting";
    error.value = "";

    try {
      const res = await fetch("/api/scan/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ db: dbId, strategy: strategy || "" }),
      });
      const data = await res.json();
      if (res.status === 409) {
        error.value = data.error || "扫描已在运行中";
        agentStatus.value = "error";
        scanning.value = false;
        return;
      }
      // WebSocket 连接由调用方通过 useWebSocket.connect() 处理
    } catch (e: any) {
      error.value = e.message;
      agentStatus.value = "error";
      scanning.value = false;
    }
  }

  async function stopScan() {
    try {
      await fetch("/api/scan/stop", { method: "POST" });
    } catch {
      // ignore
    }
    scanning.value = false;
    agentStatus.value = "offline";
  }

  async function checkStatus() {
    try {
      const res = await fetch("/api/scan/status");
      const data = await res.json();
      scanning.value = data.running;
      if (!data.running) agentStatus.value = "offline";
    } catch {
      // ignore
    }
  }

  return { scanning, agentStatus, error, startScan, stopScan, checkStatus };
}

// ── ScanConfig ───────────────────────────────────────

export function useScanConfig() {
  const config: Ref<ScanConfig> = ref({
    agent_command: "python scan.py",
    ws_port: 8765,
    default_strategy: "sample",
    sample_rows: 1000,
    overlap_threshold: 0.5,
    large_table_rules: [],
    exclude_tables: [],
  });

  async function load() {
    try {
      const res = await fetch(`${DATA_PREFIX}/scan_config.json`);
      if (res.ok) {
        config.value = await res.json();
      }
    } catch {
      // use defaults
    }
  }

  async function save() {
    try {
      await fetch("/api/data/write", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file: "scan_config.json",
          data: config.value,
        }),
      });
    } catch (e) {
      console.warn("无法保存扫描配置:", e);
    }
  }

  return { config, load, save };
}

// ── Extensions ───────────────────────────────────────

export function useExtensions() {
  const extensions: Ref<ExtensionInfo[]> = ref([]);

  async function load() {
    try {
      const res = await fetch(`${DATA_PREFIX}/extensions.json`);
      if (res.ok) {
        extensions.value = await res.json();
      }
    } catch {
      // no extensions
    }
  }

  return { extensions, load };
}
