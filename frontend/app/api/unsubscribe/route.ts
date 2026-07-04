import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
);

export async function GET(request: NextRequest) {
  try {
    const token = request.nextUrl.searchParams.get("token");

    if (!token) {
      return new Response(
        `<html><body><p>Token de cancelamento não fornecido.</p></body></html>`,
        { headers: { "Content-Type": "text/html" } }
      );
    }

    const { data, error } = await supabase
      .from("subscribers")
      .select("id")
      .eq("unsubscribe_token", token)
      .single();

    if (error || !data) {
      return new Response(
        `<html><body><p>Token inválido ou já cancelado.</p></body></html>`,
        { headers: { "Content-Type": "text/html" } }
      );
    }

    const { error: updateError } = await supabase
      .from("subscribers")
      .update({ confirmed: false })
      .eq("id", data.id);

    if (updateError) throw updateError;

    return new Response(
      `<html><body>
        <h2>Inscrição cancelada</h2>
        <p>Você não receberá mais o digest semanal de preços de CDs.</p>
        <p>Se mudar de ideia, cadastre-se novamente em <a href="${process.env.NEXT_PUBLIC_SITE_URL}/cadastro">nosso site</a>.</p>
      </body></html>`,
      { headers: { "Content-Type": "text/html" } }
    );
  } catch (error) {
    console.error("Erro ao cancelar inscrição:", error);
    return new Response(
      `<html><body><p>Erro ao cancelar inscrição. Tente novamente mais tarde.</p></body></html>`,
      { headers: { "Content-Type": "text/html" } }
    );
  }
}
