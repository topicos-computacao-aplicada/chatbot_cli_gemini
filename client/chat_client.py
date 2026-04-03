# chat_client.py
import os
import sys
import time
import requests
import uuid

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

# ============================================================================
# CONSTANTES E CONFIGURAÇÕES GLOBAIS
# ============================================================================

DEFAULT_PORT = 8000
CONNECTION_TIMEOUT = 5  # segundos
HEALTH_ENDPOINTS = ["/health", "/", "/chat", "/api/health"]

# Painéis pré-definidos para reutilização
PAINEL_BANNER = Panel.fit(
    "[bold blue]🤖 LLM ChatBot[/bold blue]\n"
    "Digite 'sair' para encerrar ou 'ajuda' para comandos",
    border_style="green",
    padding=(1, 2)
)

PAINEL_AJUDA = Panel(
    """
[b]Comandos disponíveis:[/b]
• [yellow]sair[/yellow] - Encerra o chat
• [yellow]historico[/yellow] - Mostra histórico da conversa
• [yellow]ajuda[/yellow] - Mostra esta mensagem

[b]Exemplos de perguntas:[/b]
• "Explique o que é machine learning"
• "Como funciona um neural network?"
• "Me ajude a debugar um código Python"
    """.strip(),
    title="[bold]Ajuda[/bold]",
    border_style="yellow",
    padding=(1, 2)
)


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def check_api_connection(base_url: str, timeout: int = CONNECTION_TIMEOUT) -> tuple[bool, str]:
    """
    Verifica se a API está disponível e respondendo.
    
    Args:
        base_url: URL base da API (ex: http://localhost:8000)
        timeout: Tempo máximo de espera em segundos
        
    Returns:
        tuple[bool, str]: (sucesso, mensagem descritiva)
    """
    base_url = base_url.rstrip('/')
    
    # Tenta múltiplos endpoints de health check
    for endpoint in HEALTH_ENDPOINTS:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=timeout)
            # Qualquer resposta HTTP indica que o servidor está "up"
            # (200, 400, 401, 404, 500 = servidor respondendo)
            return True, f"Conectado via {endpoint} (HTTP {response.status_code})"
        except requests.exceptions.ConnectionError:
            continue  # Tenta próximo endpoint
        except requests.exceptions.Timeout:
            continue
        except requests.exceptions.RequestException as e:
            # Outros erros (SSL, redirect, etc.) - servidor pode estar up
            return True, f"Servidor respondendo (erro esperado: {type(e).__name__})"
    
    # Nenhum endpoint respondeu
    return False, f"Não foi possível conectar em {base_url}"


def format_url(ip: str, port: int) -> str:
    """Formata URL completa a partir de IP e porta."""
    # Se já for uma URL completa, retorna como está
    if ip.startswith(('http://', 'https://')):
        return ip.rstrip('/')
    return f"http://{ip}:{port}"


# ============================================================================
# CLASSE PRINCIPAL: ChatClient
# ============================================================================

class ChatClient:
    """
    Cliente TUI para interação com API de ChatBot.
    
    Features:
    • Interface de terminal rica com Rich
    • Verificação automática de conexão
    • Sessões isoladas por UUID
    • Comandos de texto intuitivos
    • Renderização de Markdown nas respostas
    """
    
    def __init__(self, ip_servidor: str, porta: int = DEFAULT_PORT):
        """
        Inicializa o cliente de chat.
        
        Args:
            ip_servidor: IP ou hostname do servidor (ou URL completa)
            porta: Porta da API (padrão: 8000), ignorado se ip_servidor for URL
        """
        self.console = Console()
        
        # Configura URL base: prioriza variável de ambiente
        self.base_url = os.getenv(
            "API_URL", 
            format_url(ip_servidor, porta)
        )
        
        self.session_id = str(uuid.uuid4())
        self._connected = False
        
    def verify_connection(self, show_progress: bool = True) -> bool:
        """
        Verifica a conexão com a API backend.
        
        Args:
            show_progress: Exibe spinner de carregamento durante verificação
            
        Returns:
            bool: True se conectado com sucesso, False caso contrário
        """
        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Verificando conexão com {self.base_url}...", 
                    total=None
                )
                success, message = check_api_connection(self.base_url)
                progress.update(task, completed=True)
        else:
            success, message = check_api_connection(self.base_url)
        
        self._connected = success
        
        if success:
            self.console.print(
                Panel(
                    f"[green]✅ {message}[/green]\n"
                    f"[dim]Session ID: {self.session_id}[/dim]",
                    title="[bold]Conexão Estabelecida[/bold]",
                    border_style="green",
                    padding=(1, 2)
                )
            )
            # Pequena pausa para o usuário ver a mensagem
            time.sleep(0.8)
        else:
            self.console.print(
                Panel(
                    f"[red]❌ {message}[/red]\n\n"
                    "[bold]Possíveis causas:[/bold]\n"
                    "• Servidor não está rodando\n"
                    "• IP ou porta incorretos\n"
                    "• Firewall bloqueando a conexão\n"
                    "• Rede indisponível\n\n"
                    "[yellow]Sugestão:[/yellow] Verifique se o backend está ativo "
                    "e tente novamente.",
                    title="[bold]Erro de Conexão[/bold]",
                    border_style="red",
                    padding=(1, 2)
                )
            )
        
        return success
    
    def start_chat(self):
        """
        Inicia a sessão interativa de chat.
        
        Pré-requisito: verify_connection() deve ter sido chamado e retornado True.
        """
        if not self._connected:
            self.console.print(
                "[red]⚠️  Chat não pode ser iniciado sem conexão com a API.[/red]"
            )
            return
        
        self.console.print(PAINEL_BANNER)
        
        while True:
            try:
                user_input = self.console.input(
                    "\n[bold yellow]Você:[/bold yellow] "
                ).strip()
                
                # Processa comandos especiais
                cmd = user_input.lower()
                
                if cmd in ['sair', 'exit', 'quit']:
                    self.console.print("[green]Até logo! 👋[/green]")
                    break
                    
                elif cmd in ['ajuda', 'help']:
                    self.console.print(PAINEL_AJUDA)
                    continue
                    
                elif cmd == 'historico':
                    self._show_history()
                    continue
                    
                elif not user_input:
                    continue  # Ignora entrada vazia
                
                # Envia mensagem para API com feedback visual
                with self.console.status(
                    "[bold green]🤔 Processando sua mensagem...[/bold green]", 
                    spinner="dots"
                ):
                    response = self._send_message(user_input)
                
                # Exibe resposta formatada
                self._display_response(response)
                
            except KeyboardInterrupt:
                self.console.print("\n[red]⚠️  Interrompido pelo usuário (Ctrl+C)[/red]")
                break
                
            except requests.exceptions.ConnectionError:
                self.console.print(
                    Panel(
                        "[red]❌ Conexão perdida com o servidor.[/red]\n"
                        "Verifique sua conexão de rede e tente novamente.",
                        border_style="red"
                    )
                )
                break
                
            except Exception as e:
                self.console.print(f"[red]❌ Erro: {str(e)}[/red]")
                # Oferece opção de continuar ou sair
                cont = self.console.input(
                    "[yellow]Continuar tentando? (s/n): [/yellow]"
                ).strip().lower()
                if cont not in ['s', 'sim', 'y', 'yes']:
                    break
    
    def _send_message(self, message: str) -> dict:
        """
        Envia mensagem para a API e retorna a resposta.
        
        Args:
            message: Texto da mensagem do usuário
            
        Returns:
            dict: Resposta parseada da API
            
        Raises:
            Exception: Se a API retornar status diferente de 200
        """
        payload = {
            "message": message,
            "session_id": self.session_id
        }
        
        response = requests.post(
            f"{self.base_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # Timeout maior para respostas longas
        )
        
        if response.status_code != 200:
            raise Exception(
                f"API retornou erro {response.status_code}: {response.text[:200]}"
            )
        
        return response.json()
    
    def _display_response(self, response: dict):
        """
        Exibe a resposta da API formatada com Rich.
        
        Args:
            response: Dict com os campos 'response' e 'tokens_used'
        """
        response_text = response.get("response", "⚠️ Sem conteúdo na resposta")
        tokens_used = response.get("tokens_used", 0)
        
        # Renderiza Markdown para formatação rica
        md = Markdown(response_text)
        
        self.console.print(
            Panel(
                md,
                title="[bold green]🤖 Assistente[/bold green]",
                title_align="left",
                border_style="blue",
                subtitle=f"[dim]🔢 Tokens: {tokens_used}[/dim]" if tokens_used else None,
                padding=(1, 2)
            )
        )
    
    def _show_history(self):
        """Busca e exibe o histórico da conversa atual."""
        try:
            with self.console.status("[cyan]📦 Carregando histórico...[/cyan]"):
                response = requests.get(
                    f"{self.base_url}/conversations/{self.session_id}",
                    timeout=30
                )
            
            if response.status_code == 200:
                conversation = response.json()
                messages = conversation.get("messages", [])
                
                if not messages:
                    self.console.print("[yellow]ℹ️  Nenhuma mensagem no histórico.[/yellow]")
                    return
                
                self.console.print("\n[bold cyan]📜 Histórico da Conversa:[/bold cyan]")
                self.console.print(f"[dim]Total: {len(messages)} mensagem(s)[/dim]\n")
                
                for i, msg in enumerate(messages, 1):
                    role_icon = "👤" if msg["role"] == "user" else "🤖"
                    role_label = "[bold yellow]Você[/bold yellow]" if msg["role"] == "user" else "[bold green]Assistente[/bold green]"
                    
                    self.console.print(f"[dim]#{i}[/dim] {role_icon} {role_label}:")
                    self.console.print(f"  {msg['content']}")
                    if msg.get("timestamp"):
                        self.console.print(f"  [dim]🕐 {msg['timestamp']}[/dim]")
                    self.console.print()  # Linha em branco entre mensagens
                    
            else:
                self.console.print(
                    f"[yellow]⚠️  Servidor retornou {response.status_code} - "
                    f"Histórico indisponível[/yellow]"
                )
                
        except requests.exceptions.ConnectionError:
            self.console.print("[red]❌ Erro: Não foi possível conectar ao servidor.[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ Erro ao buscar histórico: {type(e).__name__} - {str(e)}[/red]")


# ============================================================================
# PONTO DE ENTRADA DA APLICAÇÃO
# ============================================================================

def print_usage():
    """Exibe mensagem de uso correto do script."""
    console = Console()
    console.print(
        Panel(
            "[bold]Uso correto:[/bold]\n\n"
            "  [cyan]python chat_client.py <IP_DO_SERVIDOR> [PORTA][/cyan]\n\n"
            "[bold]Exemplos:[/bold]\n"
            "  [green]python chat_client.py 127.0.0.1[/green]\n"
            "  [green]python chat_client.py 192.168.1.100 8000[/green]\n"
            "  [green]API_URL=https://api.com python chat_client.py ignored[/green]\n\n"
            "[bold]Variáveis de ambiente:[/bold]\n"
            "  [dim]API_URL[/dim] - URL completa da API (sobrescreve IP/porta)",
            title="[red]❌ Parâmetros insuficientes[/red]",
            border_style="red",
            padding=(1, 2)
        )
    )


def main():
    """Função principal: orquestra inicialização e execução."""
    console = Console()
    
    # Parse de argumentos da linha de comando
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    ip_servidor = sys.argv[1]
    porta = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    
    # Banner de inicialização
    console.print(
        Panel(
            f"[bold cyan]🚀 Inicializando ChatClient TUI[/bold cyan]\n"
            f"[dim]Servidor: {ip_servidor}:{porta}[/dim]\n"
            f"[dim]API_URL env: {os.getenv('API_URL', 'não definido')}[/dim]",
            border_style="cyan",
            padding=(1, 2)
        )
    )
    
    try:
        # Instancia o cliente
        client = ChatClient(ip_servidor, porta)
        
        # 🔌 VERIFICA CONEXÃO ANTES DE PROSSEGUIR
        if not client.verify_connection(show_progress=True):
            # Conexão falhou: encerra com código de erro
            console.print("\n[yellow]💡 Dica: Certifique-se que o servidor backend está rodando.[/yellow]")
            sys.exit(2)
        
        # ✅ Conexão bem-sucedida: inicia chat interativo
        client.start_chat()
        
    except KeyboardInterrupt:
        console.print("\n[red]⚠️  Encerramento forçado pelo usuário.[/red]")
        sys.exit(130)  # Código padrão para SIGINT
    except Exception as e:
        console.print(f"\n[red]❌ Erro inesperado: {type(e).__name__}: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()