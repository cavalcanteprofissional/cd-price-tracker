import SubscribeForm from "@/components/subscribe-form";

export default function CadastroPage() {
  return (
    <div style={{ maxWidth: 480, margin: "0 auto" }}>
      <h1 style={{ fontSize: 24, marginBottom: 8 }}>Receba o Digest Semanal</h1>
      <p style={{ color: "#6b7280", marginBottom: 24 }}>
        Cadastre seu email para receber toda segunda-feira um resumo com os preços
        dos CDs monitorados. Você precisará confirmar o email antes de começar a receber.
      </p>

      <SubscribeForm />
    </div>
  );
}
