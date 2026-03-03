import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { nome, empresa, whatsapp, email, plan } = body;

  if (!nome || !empresa || !whatsapp || !email) {
    return NextResponse.json(
      { error: "Todos os campos são obrigatórios" },
      { status: 400 },
    );
  }

  // TODO: integrar com backend Django ou serviço de email
  console.log("[cadastro]", { nome, empresa, whatsapp, email, plan });

  return NextResponse.json({ ok: true });
}
