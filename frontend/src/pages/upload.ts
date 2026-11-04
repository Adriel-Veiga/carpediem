import Cropper from "cropperjs";
import "cropperjs/dist/cropper.css";
import { enviarFoto } from "../api";

export function montarUpload(app: HTMLElement): void {
  app.innerHTML = `
    <main class="cartao">
      <h1>Álbum da Anna Lua</h1>
      <p>Envie sua foto da festa!</p>

      <label class="campo">Seu nome
        <input id="nome" type="text" maxlength="40" placeholder="Como você se chama?" />
      </label>

      <label class="botao" for="arquivo">Escolher foto</label>
      <input id="arquivo" type="file" accept="image/*" hidden />

      <div id="editor" hidden>
        <div class="area-previa"><img id="previa" alt="Prévia da foto" /></div>
        <div class="controles">
          <button id="girar-esq" type="button">⟲ Girar</button>
          <button id="girar-dir" type="button">Girar ⟳</button>
        </div>
        <button id="enviar" class="botao" type="button">Publicar foto</button>
      </div>

      <p id="mensagem" role="status"></p>
      <a class="link" href="#/galeria">Ver o álbum →</a>
    </main>
  `;

  function pegar<T extends HTMLElement>(id: string): T {
    const elemento = document.getElementById(id);
    if (!elemento) throw new Error(`Elemento #${id} não encontrado`);
    return elemento as T;
  }

  const nome = pegar<HTMLInputElement>("nome");
  const arquivo = pegar<HTMLInputElement>("arquivo");
  const editor = pegar<HTMLDivElement>("editor");
  const previa = pegar<HTMLImageElement>("previa");
  const botaoEnviar = pegar<HTMLButtonElement>("enviar");
  const mensagem = pegar<HTMLParagraphElement>("mensagem");

  let cropper: Cropper | null = null;

  function aviso(texto: string, erro = false): void {
    mensagem.textContent = texto;
    mensagem.className = erro ? "erro" : "ok";
  }

  arquivo.addEventListener("change", () => {
    const foto = arquivo.files?.[0];
    if (!foto) return;

    cropper?.destroy();
    cropper = null;
    aviso("");

    const endereco = URL.createObjectURL(foto);
    previa.onload = () => {
      editor.hidden = false;
      cropper = new Cropper(previa, {
        viewMode: 1,
        autoCropArea: 1,
        background: false,
      });
      URL.revokeObjectURL(endereco);
    };
    previa.onerror = () => {
      editor.hidden = true;
      aviso("Não consegui abrir essa foto. Tente outra.", true);
    };
    previa.src = endereco;
  });

  pegar<HTMLButtonElement>("girar-esq").addEventListener("click", () => cropper?.rotate(-90));
  pegar<HTMLButtonElement>("girar-dir").addEventListener("click", () => cropper?.rotate(90));

  botaoEnviar.addEventListener("click", async () => {
    if (!cropper) return;

    const nomeLimpo = nome.value.trim();
    if (!nomeLimpo) {
      aviso("Digite seu nome antes de publicar.", true);
      nome.focus();
      return;
    }

    const canvas = cropper.getCroppedCanvas({ maxWidth: 2000, maxHeight: 2000 });
    const blob = await new Promise<Blob | null>((resolver) =>
      canvas.toBlob(resolver, "image/jpeg", 0.85),
    );
    if (!blob) {
      aviso("Erro ao preparar a foto.", true);
      return;
    }

    botaoEnviar.disabled = true;
    aviso("Enviando…");
    try {
      await enviarFoto(nomeLimpo, blob);
      aviso("Foto publicada! 💖");
      cropper.destroy();
      cropper = null;
      editor.hidden = true;
      arquivo.value = "";
    } catch (erro) {
      aviso(erro instanceof Error ? erro.message : "Erro inesperado.", true);
    } finally {
      botaoEnviar.disabled = false;
    }
  });
}