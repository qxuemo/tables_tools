export interface ColumnInfo {
  name: string;
  type: string;
  comment: string | null;
}

export interface TableInfo {
  name: string;
  columns: ColumnInfo[];
  row_count: number;
}

export interface TableSchema {
  scanned_at: string;
  strategy: string;
  tables: TableInfo[];
}

export interface RelationInfo {
  from_table: string;
  from_column: string;
  to_table: string;
  to_column: string;
  match_type: "exact_name" | "keyword" | "id_pattern";
  overlap_rate: number;
  confidence: "high" | "medium" | "low";
}

export interface ConnectionInfo {
  id: string;
  name: string;
  host: string;
  port: number;
  user: string;
  password: string;
  schema: string;
  last_scan: string | null;
}

export interface LargeTableRule {
  min_rows: number;
  strategy: "sample" | "recent" | "full";
  sample_pct?: number;
  recent_days?: number;
}

export interface ScanConfig {
  agent_command: string;
  ws_port: number;
  default_strategy: "sample" | "recent" | "full";
  sample_rows: number;
  overlap_threshold: number;
  large_table_rules: LargeTableRule[];
  exclude_tables: string[];
}

export interface ExtensionInfo {
  id: string;
  name: string;
  icon: string;
  component: string;
}

export type AgentStatus = "offline" | "starting" | "scanning" | "analyzing" | "done" | "error";

export interface WSMessage {
  type: "phase" | "progress" | "candidate" | "done" | "error";
  phase?: string;
  message?: string;
  current_table?: string;
  tables_done?: number;
  tables_total?: number;
  candidates_found?: number;
  tables_scanned?: number;
  relations_found?: number;
  elapsed_seconds?: number;
  from_table?: string;
  from_column?: string;
  to_table?: string;
  to_column?: string;
  match_type?: string;
  overlap_rate?: number;
  confidence?: string;
}

export interface ScanProgress {
  phase: string;
  currentTable: string;
  tablesDone: number;
  tablesTotal: number;
  candidatesFound: number;
}
