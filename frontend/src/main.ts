import "./style.css";
import { montarUpload } from "./pages/upload";
import { montarGaleria } from "./pages/galeria";

const app = document.querySelector<HTMLDivElement>("#app")!;

function rotear(): void {
  const rota = location.hash.replace(/^#/, "") || "/";
  app.innerHTML = "";
  if (rota === "/galeria") {
    void montarGaleria(app);
  } else {
    montarUpload(app);
  }
}

window.addEventListener("hashchange", rotear);
rotear();