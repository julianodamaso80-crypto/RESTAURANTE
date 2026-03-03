import { Metadata } from "next";
import { CategoryNav } from "@/components/menu/CategoryNav";
import { ProductCard } from "@/components/menu/ProductCard";
import { CartButton } from "@/components/menu/CartButton";
import { CartDrawer } from "@/components/menu/CartDrawer";
import type { PublicCatalog, PublicCategory, Product } from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getCatalog(catalogId: string): Promise<PublicCatalog | null> {
  try {
    const res = await fetch(
      `${BASE_URL}/api/v1/catalogs/${catalogId}/public/`,
      { next: { revalidate: 60 } },
    );
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: { catalogId: string };
}): Promise<Metadata> {
  const catalog = await getCatalog(params.catalogId);
  if (!catalog) return { title: "Cardápio não encontrado" };
  return {
    title: `${catalog.store_name} — Cardápio`,
    description: `Veja o cardápio de ${catalog.store_name} e faça seu pedido online.`,
  };
}

export default async function MenuPage({
  params,
}: {
  params: { catalogId: string };
}) {
  const catalog = await getCatalog(params.catalogId);

  if (!catalog) {
    return (
      <div className="min-h-screen bg-[#0F0A06] flex items-center justify-center">
        <p className="text-[#7C5C3E] font-mono">Cardápio não encontrado</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0F0A06] text-[#FFF7ED]">
      {/* Hero */}
      <div className="px-4 py-8 text-center border-b border-[#3D2B1A]">
        <h1 className="font-bold text-2xl text-[#FFF7ED] mb-1">
          {catalog.store_name}
        </h1>
        <p className="text-[#7C5C3E] text-sm">{catalog.name}</p>
      </div>

      {/* Category navigation */}
      <CategoryNav categories={catalog.categories ?? []} />

      {/* Products by category */}
      <div className="max-w-2xl mx-auto px-4 pb-32">
        {catalog.categories?.map((category: PublicCategory) => (
          <section key={category.id} id={`cat-${category.id}`} className="pt-8">
            <h2 className="font-bold text-[#D6B896] text-lg mb-4 uppercase tracking-wider text-sm font-mono">
              {category.name}
            </h2>
            <div className="space-y-3">
              {category.products?.map((product: Product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </section>
        ))}
      </div>

      {/* Floating cart button */}
      <CartButton />

      {/* Cart drawer */}
      <CartDrawer />
    </div>
  );
}
