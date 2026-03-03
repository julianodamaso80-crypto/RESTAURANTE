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

export interface Customer {
  id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  total_orders: number;
  total_spent: string;
  last_order_at: string | null;
  rfv_score: string | null;
  created_at: string;
}

export interface StockItem {
  id: string;
  name: string;
  sku: string;
  unit: string;
  current_level: number;
  min_level: number;
  max_level: number;
  is_active: boolean;
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
