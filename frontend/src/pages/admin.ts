import {
  apagarFoto,
  baixarZip,
  definirOculta,
  entrarAdmin,
  lerToken,
  listarTodas,
  sairAdmin,
  urlAbsoluta,
} from "../api";
import type { FotoAdmin } from "../types";

export function montarAdmin(app: HTMLElement): void {
  if (lerToken()) {
    void montarPainel(app);
  } else {
    montarLogin(app);
  }
}

function montarLogin(app: HTMLElement): void {
  app.innerHTML = `
    <main class="cartao">
      <h1>Área da aniversariante</h1>
      <label class="campo">Senha
        <input id="senha" type="password" autocomplete="current-password" />
      </label>
      <button id="entrar" class="botao" type="button">Entrar</button>
      <p id="mensagem" role="status"></p>
      <a class="link" href="#/galeria">← Voltar ao álbum</a>
    </main>
  `;

  const senha = app.querySelector<HTMLInputElement>("#senha")!;
  const entrar = app.querySelector<HTMLButtonElement>("#entrar")!;
  const mensagem = app.querySelector<HTMLParagraphElement>("#mensagem")!;

  async function tentar(): Promise<void> {
    entrar.disabled = true;
    mensagem.textContent = "";
    try {
      await entrarAdmin(senha.value);
      void montarPainel(app);
    } catch (erro) {
      mensagem.textContent = erro instanceof Error ? erro.message : "Erro inesperado.";
      mensagem.className = "erro";
      entrar.disabled = false;
    }
  }

  entrar.addEventListener("click", () => void tentar());
  senha.addEventListener("keydown", (evento) => {
    if (evento.key === "Enter") void tentar();
  });
}

async function montarPainel(app: HTMLElement): Promise<void> {
  app.innerHTML = `
    <main class="galeria-pagina">
      <header class="galeria-topo">
        <h1>Painel</h1>
        <div class="acoes">
          <a class="botao" href="#/">Enviar foto</a>
          <button id="baixar" class="botao" type="button">Baixar tudo (.zip)</button>
          <button id="sair" class="botao secundario" type="button">Sair</button>
        </div>
      </header>
      <p id="estado" role="status">Carregando…</p>
      <section id="lista" class="mosaico"></section>
    </main>
  `;

  const estado = app.querySelector<HTMLParagraphElement>("#estado")!;
  const lista = app.querySelector<HTMLElement>("#lista")!;
  const baixar = app.querySelector<HTMLButtonElement>("#baixar")!;

  function mostrarErro(erro: unknown): void {
    estado.textContent = erro instanceof Error ? erro.message : "Erro inesperado.";
    estado.className = "erro";
  }

  async function agir(acao: () => Promise<void>): Promise<void> {
    try {
      await acao();
      await carregar();
    } catch (erro) {
      mostrarErro(erro);
    }
  }

  function criarCartao(foto: FotoAdmin): HTMLElement {
    const figura = document.createElement("figure");
    figura.className = `foto admin ${foto.orientation}${foto.deleted ? " oculta" : ""}`;

    const imagem = document.createElement("img");
    imagem.src = urlAbsoluta(foto.thumb_url);
    imagem.alt = `Foto enviada por ${foto.author_name}`;

    const legenda = document.createElement("figcaption");
    const nome = document.createElement("span");
    nome.textContent = foto.deleted ? `${foto.author_name} (oculta)` : foto.author_name;

    const ocultar = document.createElement("button");
    ocultar.type = "button";
    ocultar.textContent = foto.deleted ? "Restaurar" : "Ocultar";
    ocultar.addEventListener("click", () =>
      void agir(() => definirOculta(foto.id, !foto.deleted)),
    );

    const apagar = document.createElement("button");
    apagar.type = "button";
    apagar.textContent = "Apagar";
    apagar.addEventListener("click", () => {
      const certeza = confirm(
        `Apagar para sempre a foto de ${foto.author_name}? Isso não pode ser desfeito.`,
      );
      if (certeza) void agir(() => apagarFoto(foto.id));
    });

    legenda.append(nome, ocultar, apagar);
    figura.append(imagem, legenda);
    return figura;
  }

  async function carregar(): Promise<void> {
    let fotos: FotoAdmin[];
    try {
      fotos = await listarTodas();
    } catch (erro) {
      if (!lerToken()) {
        montarLogin(app); // a sessão expirou
        return;
      }
      mostrarErro(erro);
      return;
    }
    estado.className = "";
    estado.textContent = fotos.length === 0 ? "Nenhuma foto ainda." : `${fotos.length} foto(s)`;
    lista.replaceChildren(...fotos.map(criarCartao));
  }

  baixar.addEventListener("click", async () => {
    baixar.disabled = true;
    try {
      const arquivo = await baixarZip();
      const endereco = URL.createObjectURL(arquivo);
      const link = document.createElement("a");
      link.href = endereco;
      link.download = "album-anna-lua.zip";
      link.click();
      URL.revokeObjectURL(endereco);
    } catch (erro) {
      mostrarErro(erro);
    } finally {
      baixar.disabled = false;
    }
  });

  app.querySelector<HTMLButtonElement>("#sair")!.addEventListener("click", () => {
    sairAdmin();
    location.hash = "#/galeria";
  });

  await carregar();
}