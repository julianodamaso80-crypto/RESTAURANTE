"use client";

import { Header } from "@/components/layout/Header";
import { EmptyState } from "@/components/shared/EmptyState";
import { Store } from "lucide-react";

export default function MenuPage() {
  return (
    <>
      <Header title="Cardápio" />
      <div className="p-6">
        <EmptyState
          icon={Store}
          title="Cardápio vazio"
          description="Adicione categorias e produtos ao seu cardápio."
        />
      </div>
    </>
  );
}
