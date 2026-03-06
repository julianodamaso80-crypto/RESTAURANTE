import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Product, ModifierOption } from "@/types/api";

export interface CartItem {
  id: string;
  product: Product;
  quantity: number;
  selectedModifiers: ModifierOption[];
  notes: string;
  unitPriceCents: number;
  totalPriceCents: number;
}

interface CartState {
  items: CartItem[];
  isOpen: boolean;
  catalogId: string | null;
  addItem: (
    product: Product,
    quantity: number,
    modifiers: ModifierOption[],
    notes: string,
    catalogId: string,
  ) => void;
  removeItem: (id: string) => void;
  updateQuantity: (id: string, quantity: number) => void;
  clearCart: () => void;
  openCart: () => void;
  closeCart: () => void;
  totalPriceCents: () => number;
  totalItems: () => number;
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      isOpen: false,
      catalogId: null,

      addItem: (product, quantity, modifiers, notes, catalogId) => {
        // If adding from a different catalog, clear the cart
        const current = get().catalogId;
        if (current && current !== catalogId) {
          set({ items: [], catalogId });
        }

        const modifierTotal = modifiers.reduce(
          (sum, m) => sum + m.price_delta_cents,
          0,
        );
        const unitPriceCents = product.price_cents + modifierTotal;
        const item: CartItem = {
          id: Math.random().toString(36).slice(2),
          product,
          quantity,
          selectedModifiers: modifiers,
          notes,
          unitPriceCents,
          totalPriceCents: unitPriceCents * quantity,
        };
        set((state) => ({
          items: [...state.items, item],
          isOpen: true,
          catalogId,
        }));
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
                    ? { ...i, quantity, totalPriceCents: i.unitPriceCents * quantity }
                    : i,
                ),
        })),

      clearCart: () => set({ items: [], catalogId: null }),
      openCart: () => set({ isOpen: true }),
      closeCart: () => set({ isOpen: false }),
      totalPriceCents: () =>
        get().items.reduce((sum, i) => sum + i.totalPriceCents, 0),
      totalItems: () =>
        get().items.reduce((sum, i) => sum + i.quantity, 0),
    }),
    {
      name: "mesamestre-cart",
      partialize: (state) => ({
        items: state.items,
        catalogId: state.catalogId,
      }),
    },
  ),
);
