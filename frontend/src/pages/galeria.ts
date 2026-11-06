import { listarFotos, urlAbsoluta } from "../api";
import type { Foto } from "../types";

export async function montarGaleria(app: HTMLElement): Promise<void> {
  app.innerHTML = `
        <dialog id="visualizador" class="visualizador">
        <div class="conteudo">
          <button id="fechar" type="button" aria-label="Fechar">✕</button>
          <img id="foto-grande" alt="" />
          <p id="foto-autor"></p>
        </div>
      </dialog>
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
    const dialogo = app.querySelector<HTMLDialogElement>("#visualizador")!;
  const fotoGrande = app.querySelector<HTMLImageElement>("#foto-grande")!;
  const fotoAutor = app.querySelector<HTMLParagraphElement>("#foto-autor")!;

  app.querySelector<HTMLButtonElement>("#fechar")!.addEventListener("click", () => dialogo.close());
  // Clicar no fundo escuro (fora da foto) também fecha
  dialogo.addEventListener("click", (evento) => {
    if (evento.target === dialogo) dialogo.close();
  });

  function abrir(foto: Foto): void {
    fotoGrande.src = urlAbsoluta(foto.url);
    fotoGrande.alt = `Foto enviada por ${foto.author_name}`;
    fotoAutor.textContent = `Enviada por ${foto.author_name}`;
    dialogo.showModal();
  }

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

    figura.tabIndex = 0; // permite navegar com o teclado
    figura.addEventListener("click", () => abrir(foto));
    figura.addEventListener("keydown", (evento) => {
      if (evento.key === "Enter") abrir(foto);
    });

    figura.append(imagem, legenda);
    mosaico.append(figura);
  });
}