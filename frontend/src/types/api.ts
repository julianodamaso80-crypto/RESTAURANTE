export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type OrderStatus =
  | "PENDING"
  | "CONFIRMED"
  | "IN_PREPARATION"
  | "READY"
  | "DISPATCHED"
  | "DELIVERED"
  | "CANCELLED";

export interface OrderItem {
  id: string;
  external_item_id: string;
  name: string;
  quantity: number;
  unit_price: string;
  total_price: string;
  notes: string;
  modifiers: OrderItemModifier[];
}

export interface OrderItemModifier {
  name: string;
  quantity: number;
  unit_price: string;
}

export interface Order {
  id: string;
  display_id: string;
  channel: string;
  status: OrderStatus;
  customer_name: string;
  customer_phone: string;
  items: OrderItem[];
  subtotal: string;
  discount: string;
  delivery_fee: string;
  total: string;
  notes: string;
  placed_at: string;
  confirmed_at: string | null;
  ready_at: string | null;
  delivered_at: string | null;
  cancelled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface KDSStation {
  id: string;
  name: string;
  station_type: string;
  is_active: boolean;
  store: string;
}

export type KDSTicketStatus = "WAITING" | "IN_PROGRESS" | "DONE" | "RECALLED";

export interface KDSTicket {
  id: string;
  order: string;
  order_display_number: string;
  station: string;
  status: KDSTicketStatus;
  items: OrderItem[];
  enqueued_at: string;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface Product {
  id: string;
  name: string;
  description: string;
  sku: string;
  base_price: string;
  is_active: boolean;
  category: string;
  modifier_groups: ModifierGroup[];
  image_url: string | null;
}

export interface ModifierGroup {
  id: string;
  name: string;
  min_selections: number;
  max_selections: number;
  options: ModifierOption[];
}

export interface ModifierOption {
  id: string;
  name: string;
  price: string;
  is_active: boolean;
}

export interface CustomerIdentity {
  id: string;
  type: string;
  value: string;
  is_verified: boolean;
  source: string;
  created_at: string;
}

export interface ConsentRecord {
  id: string;
  channel: string;
  status: "GRANTED" | "REVOKED";
  source: string;
  legal_basis: string;
  created_at: string;
}

export interface CustomerEvent {
  id: string;
  event_type: string;
  payload: Record<string, unknown>;
  occurred_at: string;
}

export interface Customer {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  rfv_recency_days: number | null;
  rfv_frequency: number | null;
  rfv_monetary_cents: number | null;
  rfv_last_order_at: string | null;
  rfv_calculated_at: string | null;
  is_active: boolean;
  is_anonymous: boolean;
  identities: CustomerIdentity[];
  consent_summary: Record<string, boolean>;
  created_at: string;
  updated_at: string;
}

export interface CustomerSegment {
  id: string;
  name: string;
  description: string;
  criteria: { criteria: string; value: unknown }[];
  estimated_size: number;
  created_at: string;
}

export interface CampaignTemplate {
  id: string;
  name: string;
  channel: string;
  subject: string;
  body: string;
  created_at: string;
}

export type CampaignStatusType = "DRAFT" | "SCHEDULED" | "RUNNING" | "COMPLETED" | "CANCELLED";

export interface CampaignRun {
  id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  total_recipients: number;
  sent_count: number;
  delivered_count: number;
  failed_count: number;
  opted_out_count: number;
  error_detail: string;
}

export interface Campaign {
  id: string;
  name: string;
  status: CampaignStatusType;
  segment: string;
  segment_name: string;
  template: string;
  template_name: string;
  scheduled_at: string | null;
  runs: CampaignRun[];
  created_at: string;
  updated_at: string;
}

export interface BillingQuota {
  max_contacts: number;
  current_period_contacts: number;
  usage_pct: number;
  is_blocked: boolean;
  is_near_limit: boolean;
  period_start: string;
  updated_at: string;
}

export interface StockLevel {
  current_quantity: string;
  is_below_minimum: boolean;
  last_movement_at: string | null;
  calculated_at: string | null;
}

export interface StockItem {
  id: string;
  name: string;
  unit: string;
  minimum_stock: string;
  is_active: boolean;
  notes: string;
  level: StockLevel | null;
  created_at: string;
}

export type MovementType = "ENTRADA" | "SAIDA" | "AJUSTE" | "PERDA" | "INVENTARIO";

export interface StockMovement {
  id: string;
  stock_item: string;
  type: MovementType;
  quantity: string;
  notes: string;
  reference_type: string;
  reference_id: string;
  occurred_at: string;
}

export interface StockAlert {
  id: string;
  stock_item: string;
  stock_item_name: string;
  stock_item_unit: string;
  current_qty: number;
  minimum_qty: number;
  is_resolved: boolean;
  created_at: string;
  resolved_at: string | null;
}

// Public catalog (SSR menu page)
export interface PublicCatalog {
  id: string;
  name: string;
  store_name: string;
  categories: PublicCategory[];
}

export interface PublicCategory {
  id: string;
  name: string;
  sort_order: number;
  products: Product[];
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
}
