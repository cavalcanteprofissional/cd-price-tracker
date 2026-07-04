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
        `<html><body><p>Token de confirmação não fornecido.</p></body></html>`,
        { headers: { "Content-Type": "text/html" } }
      );
    }

    const { data, error } = await supabase
      .from("subscribers")
      .select("id, confirmed")
      .eq("confirmation_token", token)
      .single();

    if (error || !data) {
      return new Response(
        `<html><body><p>Token inválido ou expirado. Tente se cadastrar novamente.</p></body></html>`,
        { headers: { "Content-Type": "text/html" } }
      );
    }

    if (data.confirmed) {
      return new Response(
        `<html><body><p>Email já confirmado! Você já está recebendo o digest semanal.</p></body></html>`,
        { headers: { "Content-Type": "text/html" } }
      );
    }

    const { error: updateError } = await supabase
      .from("subscribers")
      .update({ confirmed: true })
      .eq("id", data.id);

    if (updateError) throw updateError;

    return new Response(
      `<html><body>
        <h2>Email confirmado com sucesso!</h2>
        <p>Agora você passará a receber o digest semanal de preços de CDs toda segunda-feira.</p>
      </body></html>`,
      { headers: { "Content-Type": "text/html" } }
    );
  } catch (error) {
    console.error("Erro ao confirmar:", error);
    return new Response(
      `<html><body><p>Erro ao confirmar email. Tente novamente mais tarde.</p></body></html>`,
      { headers: { "Content-Type": "text/html" } }
    );
  }
}
