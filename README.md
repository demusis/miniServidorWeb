# Mini Servidor Web (Desktop)

Aplicativo desktop em Python/Tkinter que inicia um pequeno servidor web local para abrir sites estáticos (arquivos `.html` ou pacotes `.zip` com um site completo) diretamente no navegador padrão.

---

## Funcionalidades

- **Autodetecção de página inicial**  
  Procura automaticamente por `index.html`, `default.html`, `home.html` ou `main.html` na pasta onde o programa está.

- **Suporte a pacotes ZIP**  
  Se encontrar um arquivo `.zip` na pasta, descompacta em uma pasta temporária e serve o conteúdo.

- **Seleção manual de conteúdo**  
  Se nada for encontrado automaticamente, abre uma janela para você escolher:
  - um arquivo `.html`, ou  
  - um arquivo `.zip` contendo o site.

- **Servidor HTTP local**  
  Usa a biblioteca padrão do Python (`http.server` + `socketserver`) escutando em `127.0.0.1` em uma porta livre escolhida automaticamente.

- **Abertura automática no navegador**  
  Após iniciar o servidor, abre o navegador padrão apontando para a página HTML encontrada.

- **Atalho global [ESC]**  
  A tecla **ESC** fecha a aplicação em qualquer fase (tela de carregamento, seleção de arquivo ou janela de status).

- **Log detalhado**  
  Gera um arquivo `web_server_debug.log` com mensagens de debug e requisições HTTP, útil para resolver problemas.
