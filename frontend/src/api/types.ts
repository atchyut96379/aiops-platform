export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
}

export interface DashboardSummary {
  total_assets: number;
  healthy_assets: number;
  open_alerts: number;
  critical_alerts: number;
  open_incidents: number;
  closed_incidents: number;
  alerts_by_level: Record<string, number>;
  incidents_by_severity: Record<string, number>;
  assets_by_status: Record<string, number>;
}

export interface Asset {
  id: number;
  hostname: string;
  asset_type: string;
  ip_address?: string;
  status: string;
  environment: string;
}

export interface Alert {
  id: number;
  alert_type: string;
  level: string;
  status: string;
  acknowledged: boolean;
  resolved: boolean;
  asset_id?: number;
  created_at?: string;
}

export interface Incident {
  id: number;
  title: string;
  description?: string;
  severity: string;
  status: string;
  incident_type: string;
  asset_id?: number;
  created_at?: string;
}

export interface AuditLog {
  id: number;
  action: string;
  user_id?: number;
  resource_type?: string;
  resource_id?: string;
  created_at?: string;
}

export interface NotificationChannel {
  id: number;
  name: string;
  channel_type: string;
  min_alert_level: string;
  is_active: boolean;
}

export interface KnowledgeDocument {
  id: number;
  title: string;
  category: string;
  content: string;
  tags?: string;
}
