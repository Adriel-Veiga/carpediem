export type Orientacao = "vertical" | "horizontal" | "quadrada";

export interface FotoEnviada {
  id: string;
  author_name: string;
  width: number;
  height: number;
  orientation: Orientacao;
}