import sys
import os
import time
import logging
import threading
import webbrowser
import glob
import zipfile
import tempfile
import socketserver
import http.server
import tkinter as tk
from tkinter import messagebox, filedialog, ttk

# --- Configurações Globais ---
NOMES_PADRAO = ["index.html", "default.html", "home.html", "main.html"]
ARQUIVO_LOG = "web_server_debug.log"
PORTA_SERVIDOR = 0 

class MiniWebServerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.diretorio_base = self._obter_diretorio_execucao()
        self.server_httpd = None
        self.thread_servidor = None
        
        # Binding Global: A tecla ESC fecha a aplicação em qualquer estágio
        self.root.bind('<Escape>', self._encerrar)
        
        # Inicialização
        self._configurar_logging()
        logging.info("=== Inicializando Mini Servidor Web ===")
        self._configurar_splash()

    def _obter_diretorio_execucao(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def _configurar_logging(self):
        caminho_log = os.path.join(self.diretorio_base, ARQUIVO_LOG)
        logging.basicConfig(
            filename=caminho_log,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def _configurar_splash(self):
        self.root.title("Carregando...")
        self.root.overrideredirect(True)
        
        # Geometria
        largura = 400
        altura = 180 # Aumentado ligeiramente para caber a instrução
        x_pos = (self.root.winfo_screenwidth() - largura) // 2
        y_pos = (self.root.winfo_screenheight() - altura) // 2
        self.root.geometry(f"{largura}x{altura}+{x_pos}+{y_pos}")
        
        # Design
        frame = tk.Frame(self.root, bg="#34495e", relief="raised", bd=2)
        frame.pack(expand=True, fill="both")
        
        lbl_titulo = tk.Label(frame, text="Mini Servidor Web", font=("Segoe UI", 18, "bold"), fg="white", bg="#34495e")
        lbl_titulo.pack(pady=(20, 5))
        
        self.lbl_status = tk.Label(frame, text="Inicializando ambiente...", font=("Segoe UI", 9), fg="#bdc3c7", bg="#34495e")
        self.lbl_status.pack(pady=2)
        
        self.barra_progresso = ttk.Progressbar(frame, orient="horizontal", length=300, mode="indeterminate")
        self.barra_progresso.pack(pady=10)
        self.barra_progresso.start(15)

        # --- Instrução do Atalho ---
        lbl_atalho = tk.Label(frame, text="[ESC] para cancelar e sair", font=("Consolas", 8), fg="#95a5a6", bg="#34495e")
        lbl_atalho.pack(side="bottom", pady=10)

    def atualizar_status(self, mensagem):
        logging.info(f"Status: {mensagem}")
        self.root.after(0, lambda: self.lbl_status.config(text=mensagem))

    def _exibir_erro_fatal(self, titulo, mensagem):
        logging.error(f"Erro Fatal: {titulo} - {mensagem}")
        # Desvincula o ESC temporariamente para evitar conflito com o Enter do messagebox, se necessário,
        # mas aqui mantemos para permitir fechamento forçado.
        messagebox.showerror(titulo, mensagem)
        self._encerrar()

    def iniciar(self):
        thread_trabalho = threading.Thread(target=self._fluxo_principal, daemon=True)
        thread_trabalho.start()
        self.root.mainloop()

    def _fluxo_principal(self):
        try:
            time.sleep(1)
            
            self.atualizar_status("Verificando recursos locais...")
            caminho_html = self._localizar_html(self.diretorio_base)
            diretorio_servidor = None

            if caminho_html:
                diretorio_servidor = os.path.dirname(caminho_html)
            else:
                zips = glob.glob(os.path.join(self.diretorio_base, "*.zip"))
                if zips:
                    self.atualizar_status("Descompactando pacote de dados...")
                    diretorio_servidor = self._processar_zip(zips[0])
                else:
                    self.atualizar_status("Aguardando entrada do usuário...")
                    self.root.after(0, self._solicitar_manual)
                    return 

            if diretorio_servidor:
                self._finalizar_boot(diretorio_servidor)
            else:
                self.root.after(0, lambda: self._exibir_erro_fatal("Erro", "Nenhum conteúdo válido."))

        except Exception as e:
            logging.exception("Erro no fluxo principal")
            self.root.after(0, lambda: self._exibir_erro_fatal("Falha Crítica", str(e)))

    def _processar_zip(self, caminho_zip):
        try:
            dir_temp = tempfile.mkdtemp(prefix="web_cache_")
            with zipfile.ZipFile(caminho_zip, 'r') as zf:
                zf.extractall(dir_temp)
            
            caminho_html = self._localizar_html(dir_temp)
            if not caminho_html:
                for root, _, _ in os.walk(dir_temp):
                    caminho_html = self._localizar_html(root)
                    if caminho_html: break
            
            if caminho_html:
                return os.path.dirname(caminho_html)
            return None
        except Exception as e:
            logging.error(f"Erro ZIP: {e}")
            raise e

    def _localizar_html(self, diretorio):
        for nome in NOMES_PADRAO:
            path = os.path.join(diretorio, nome)
            if os.path.exists(path): return path
        arquivos = glob.glob(os.path.join(diretorio, "*.html"))
        return arquivos[0] if arquivos else None

    def _solicitar_manual(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o Site ou Pacote ZIP",
            filetypes=[("Conteúdo Web", "*.html *.zip")]
        )
        if not caminho:
            self._encerrar()
            return
            
        threading.Thread(target=self._processar_manual_thread, args=(caminho,), daemon=True).start()

    def _processar_manual_thread(self, caminho):
        try:
            dir_servidor = None
            if caminho.lower().endswith(".zip"):
                self.atualizar_status("Processando arquivo selecionado...")
                dir_servidor = self._processar_zip(caminho)
            else:
                dir_servidor = os.path.dirname(caminho)
            
            if dir_servidor:
                self._finalizar_boot(dir_servidor)
            else:
                self.root.after(0, lambda: self._exibir_erro_fatal("Erro", "Conteúdo inválido."))
        except Exception as e:
             self.root.after(0, lambda: self._exibir_erro_fatal("Erro", str(e)))

    def _iniciar_servidor(self, diretorio):
        try:
            handler = http.server.SimpleHTTPRequestHandler
            class HandlerCustomizado(handler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=diretorio, **kwargs)
                def log_message(self, format, *args):
                    logging.info(f"REQ: {format % args}")

            self.server_httpd = socketserver.TCPServer(("127.0.0.1", 0), HandlerCustomizado)
            porta = self.server_httpd.server_address[1]
            
            self.thread_servidor = threading.Thread(target=self.server_httpd.serve_forever, daemon=True)
            self.thread_servidor.start()
            return porta
        except Exception as e:
            raise e

    def _finalizar_boot(self, diretorio_servidor):
        self.atualizar_status("Iniciando serviços de rede...")
        porta = self._iniciar_servidor(diretorio_servidor)
        
        self.atualizar_status("Carregando navegador...")
        url = f"http://127.0.0.1:{porta}/"
        html_found = self._localizar_html(diretorio_servidor)
        if html_found: url += os.path.basename(html_found)

        webbrowser.open(url, new=2)
        self.root.after(1000, self._modo_servidor_ativo)

    def _modo_servidor_ativo(self):
        self.root.overrideredirect(False)
        for widget in self.root.winfo_children(): widget.destroy()

        largura, altura = 300, 100
        x_pos = self.root.winfo_screenwidth() - largura - 20
        y_pos = self.root.winfo_screenheight() - altura - 60
        
        self.root.geometry(f"{largura}x{altura}+{x_pos}+{y_pos}")
        self.root.title("Status")
        self.root.configure(bg="#ecf0f1")
        
        lbl = tk.Label(self.root, text="Servidor Web Ativo", font=("Segoe UI", 10, "bold"), bg="#ecf0f1", fg="#2c3e50")
        lbl.pack(pady=(10, 5))
        
        # Botão com indicação do atalho
        btn_sair = tk.Button(self.root, text="Encerrar [ESC]", command=self._encerrar, bg="#c0392b", fg="white", width=15)
        btn_sair.pack(pady=5)
        
        self.root.protocol("WM_DELETE_WINDOW", self._encerrar)

    def _encerrar(self, event=None):
        """
        Encerra a aplicação de forma segura.
        Aceita argumento 'event' para compatibilidade com bind de teclado.
        """
        logging.info(f"Encerrando aplicação. Trigger: {'Teclado/Evento' if event else 'Botão/Sistema'}")
        if self.server_httpd:
            self.server_httpd.shutdown()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = MiniWebServerApp()
    app.iniciar()