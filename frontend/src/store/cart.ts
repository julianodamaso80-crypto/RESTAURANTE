import { create } from "zustand";
import type { Product, ModifierOption } from "@/types/api";

export interface CartItem {
  id: string;
  product: Product;
  quantity: number;
  selectedModifiers: ModifierOption[];
  notes: string;
  unitPrice: number;
  totalPrice: number;
}

interface CartState {
  items: CartItem[];
  isOpen: boolean;
  addItem: (
    product: Product,
    quantity: number,
    modifiers: ModifierOption[],
    notes: string,
  ) => void;
  removeItem: (id: string) => void;
  updateQuantity: (id: string, quantity: number) => void;
  clearCart: () => void;
  openCart: () => void;
  closeCart: () => void;
  totalPrice: () => number;
  totalItems: () => number;
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  isOpen: false,

  addItem: (product, quantity, modifiers, notes) => {
    const modifierTotal = modifiers.reduce(
      (sum, m) => sum + parseFloat(m.price),
      0,
    );
    const unitPrice = parseFloat(product.base_price) + modifierTotal;
    const item: CartItem = {
      id: Math.random().toString(36).slice(2),
      product,
      quantity,
      selectedModifiers: modifiers,
      notes,
      unitPrice,
      totalPrice: unitPrice * quantity,
    };
    set((state) => ({ items: [...state.items, item], isOpen: true }));
  },

  removeItem: (id) =>
    set((state) => ({ items: state.items.filter((i) => i.id !== id) })),

  updateQuantity: (id, quantity) =>
    set((state) => ({
      items:
        quantity <= 0
          ? state.items.filter((i) => i.id !== id)
          : state.items.map((i) =>
              i.id === id
                ? { ...i, quantity, totalPrice: i.unitPrice * quantity }
                : i,
            ),
    })),

  clearCart: () => set({ items: [] }),
  openCart: () => set({ isOpen: true }),
  closeCart: () => set({ isOpen: false }),
  totalPrice: () => get().items.reduce((sum, i) => sum + i.totalPrice, 0),
  totalItems: () => get().items.reduce((sum, i) => sum + i.quantity, 0),
}));
