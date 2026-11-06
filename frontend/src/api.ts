import type { Foto, FotoAdmin, FotoEnviada } from "./types";

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

export async function listarFotos(): Promise<Foto[]> {
  const resposta = await fetch(`${API_URL}/photos`);
  if (!resposta.ok) throw new Error("Não foi possível carregar o álbum.");
  return resposta.json();
}

export function urlAbsoluta(caminho: string): string {
  return `${API_URL}${caminho}`;
}

const CHAVE_TOKEN = "admin_token";

export function lerToken(): string | null {
  return sessionStorage.getItem(CHAVE_TOKEN);
}

export function sairAdmin(): void {
  sessionStorage.removeItem(CHAVE_TOKEN);
}

export async function entrarAdmin(senha: string): Promise<void> {
  const resposta = await fetch(`${API_URL}/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password: senha }),
  });
  if (!resposta.ok) {
    const erro = await resposta.json().catch(() => null);
    throw new Error(erro?.detail ?? "Não foi possível entrar.");
  }
  const dados: { token: string } = await resposta.json();
  sessionStorage.setItem(CHAVE_TOKEN, dados.token);
}

async function chamarAdmin(caminho: string, opcoes: RequestInit = {}): Promise<Response> {
  const resposta = await fetch(`${API_URL}${caminho}`, {
    ...opcoes,
    headers: { ...opcoes.headers, Authorization: `Bearer ${lerToken() ?? ""}` },
  });
  if (resposta.status === 401) {
    sairAdmin();
    throw new Error("Sessão expirada. Entre de novo.");
  }
  if (!resposta.ok) throw new Error("A operação não funcionou. Tente de novo.");
  return resposta;
}

export async function listarTodas(): Promise<FotoAdmin[]> {
  return (await chamarAdmin("/admin/photos")).json();
}

export async function definirOculta(id: string, oculta: boolean): Promise<void> {
  await chamarAdmin(`/admin/photos/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ deleted: oculta }),
  });
}

export async function apagarFoto(id: string): Promise<void> {
  await chamarAdmin(`/admin/photos/${id}`, { method: "DELETE" });
}

export async function baixarZip(): Promise<Blob> {
  return (await chamarAdmin("/admin/download")).blob();
}