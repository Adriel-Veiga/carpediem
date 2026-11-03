import type { FotoEnviada } from "./types";

const API_URL: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export async function enviarFoto(nome: string, foto: Blob): Promise<FotoEnviada> {
  const dados = new FormData();
  dados.append("author_name", nome);
  dados.append("file", foto, "foto.jpg");

  const resposta = await fetch(`${API_URL}/photos`, {
    method: "POST",
    body: dados,
  });

  if (!resposta.ok) {
    const erro = await resposta.json().catch(() => null);
    throw new Error(erro?.detail ?? "Não foi possível enviar a foto.");
  }
  return resposta.json();
}