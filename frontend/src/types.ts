export type Orientacao = "vertical" | "horizontal" | "quadrada";

export interface FotoEnviada {
  id: string;
  author_name: string;
  width: number;
  height: number;
  orientation: Orientacao;
}

export interface Foto extends FotoEnviada {
  url: string;
  thumb_url: string;
}

export interface FotoAdmin extends Foto {
  deleted: boolean;
}