import { listarFotos, urlAbsoluta } from "../api";
import type { Foto } from "../types";

export async function montarGaleria(app: HTMLElement): Promise<void> {
  app.innerHTML = `
    <main class="galeria-pagina">
      <header class="galeria-topo">
        <h1>Álbum da Anna Lua</h1>
        <a class="botao" href="#/">Enviar foto</a>
      </header>
      <p id="estado" role="status">Carregando fotos…</p>
      <section id="mosaico" class="mosaico"></section>
    </main>
  `;

  const estado = app.querySelector<HTMLParagraphElement>("#estado")!;
  const mosaico = app.querySelector<HTMLElement>("#mosaico")!;

  let fotos: Foto[];
  try {
    fotos = await listarFotos();
  } catch (erro) {
    estado.textContent = erro instanceof Error ? erro.message : "Erro inesperado.";
    estado.className = "erro";
    return;
  }

  if (fotos.length === 0) {
    estado.textContent = "Ainda não há fotos. Seja o primeiro a enviar! 💖";
    return;
  }
  estado.textContent = "";

  fotos.forEach((foto, indice) => {
    const figura = document.createElement("figure");
    figura.className = `foto ${foto.orientation}`;
    figura.style.setProperty("--atraso", `${Math.min(indice, 20) * 60}ms`);

    const imagem = document.createElement("img");
    imagem.src = urlAbsoluta(foto.thumb_url);
    imagem.alt = `Foto enviada por ${foto.author_name}`;
    imagem.loading = "lazy";

    const legenda = document.createElement("figcaption");
    legenda.textContent = foto.author_name;

    figura.append(imagem, legenda);
    mosaico.append(figura);
  });
}