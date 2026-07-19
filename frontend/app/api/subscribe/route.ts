import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { Resend } from "resend";
import { randomUUID } from "crypto";

function getResend(): Resend | null {
  const key = process.env.RESEND_API_KEY;
  if (!key) return null;
  return new Resend(key);
}

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!,
  );
}

const recentSubscriptions = new Map<string, number>();

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json();

    if (!email || typeof email !== "string") {
      return NextResponse.json({ error: "Email inválido" }, { status: 400 });
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json({ error: "Formato de email inválido" }, { status: 400 });
    }

    const now = Date.now();
    const lastAttempt = recentSubscriptions.get(email.toLowerCase());
    if (lastAttempt && now - lastAttempt < 60000) {
      return NextResponse.json({ error: "Aguarde 1 minuto antes de tentar novamente." }, { status: 429 });
    }
    recentSubscriptions.set(email.toLowerCase(), now);

    const confirmationToken = randomUUID();
    const unsubscribeToken = randomUUID();

    const supabase = getSupabase();
    const { error: insertError } = await supabase
      .from("subscribers")
      .insert({
        email: email.toLowerCase().trim(),
        confirmed: false,
        confirmation_token: confirmationToken,
        unsubscribe_token: unsubscribeToken,
      });

    if (insertError) {
      if (insertError.code === "23505") {
        return NextResponse.json(
          { error: "Este email já está cadastrado." },
          { status: 409 }
        );
      }
      throw insertError;
    }

    const resend = getResend();
    if (!resend) {
      console.warn("Resend não configurado (RESEND_API_KEY ausente)");
      return NextResponse.json({ message: "Email cadastrado com sucesso!" });
    }

    const confirmUrl = `${process.env.NEXT_PUBLIC_SITE_URL}/api/confirm?token=${confirmationToken}`;

    await resend.emails.send({
      from: process.env.RESEND_FROM_EMAIL!,
      to: email.toLowerCase().trim(),
      subject: "Confirme seu email - CD Price Tracker",
      html: `
        <h2>Confirme seu cadastro</h2>
        <p>Clique no link abaixo para confirmar seu email e começar a receber o digest semanal de preços de CDs:</p>
        <p><a href="${confirmUrl}">${confirmUrl}</a></p>
        <p>Se você não se cadastrou, ignore este email.</p>
      `,
    });

    return NextResponse.json({ message: "Email cadastrado com sucesso!" });
  } catch (error) {
    console.error("Erro ao cadastrar subscriber:", error);
    return NextResponse.json(
      { error: "Erro interno ao processar cadastro" },
      { status: 500 }
    );
  }
}
