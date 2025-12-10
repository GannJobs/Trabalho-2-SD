from mpi4py import MPI
import sys
import time

# =============================================================================
# DEFINIÇÕES E CONFIGURAÇÃO DO MPI
# =============================================================================

TAG_ELEICAO = 1     # Mensagem de um processo menor perguntando: "Tem alguém maior aí?"
TAG_OK = 2          # Resposta de um processo maior: "Eu estou vivo, pare de tentar ser líder."
TAG_LIDER = 3       # Comunicado final: "Eu ganhei a eleição, atualizem seus registros."

# Inicializa o comunicador global (o canal onde todos os processos conversam)
comm = MPI.COMM_WORLD

# Quem sou eu? (Rank é o ID do processo, de 0 a N-1)
my_rank = comm.Get_rank()

# Quantos somos? (Número total de processos iniciados com -np)
num_procs = comm.Get_size()

# Objeto status: Usado no recv() para descobrir quem mandou a mensagem (source) e qual a tag
status = MPI.Status()

# Dicionário para guardar o cenário da simulação (quem morre e quem inicia)
config = {'morto': -1, 'iniciador': -1}

# =============================================================================
# ALGORITMO
# =============================================================================

def tentar_eleicao(eu, total, morto):
    """
    Um processo tenta encontrar alguém com ID maior que o dele vivo.
    - Se encontrar: Passa a responsabilidade para o maior e desiste.
    - Se não encontrar: Assume a liderança.
    """
    existe_maior_vivo = False
    
    # --- PASSO 1 ---
    # Varre apenas os IDs maiores que o meu (eu + 1 até o fim)
    for superior in range(eu + 1, total):
        
        # Se não houver resposta, assumimos que o processo caiu.
        # Aqui, como sabemos quem é o 'morto', apenas pulamos o envio para economizar tempo.
        if superior == morto:
            continue 
        
        # Envia mensagem de ELEIÇÃO para o processo superior
        print(f"[Processo {eu}] Enviando ELEICAO para superior {superior}...")
        comm.send({'tipo': 'ELEICAO'}, dest=superior, tag=TAG_ELEICAO)
        
        # Marcamos que pelo menos uma mensagem foi enviada para um candidato válido
        existe_maior_vivo = True
    
    # --- PASSO 2 ---
    if existe_maior_vivo:
        # Se enviei mensagem para alguém maior, pela regra do Valentão, eu perdi.
        # O maior tem prioridade. Fico bloqueado aqui esperando ele confirmar (OK)
        # que recebeu minha mensagem e vai assumir o controle.
        msg = comm.recv(source=MPI.ANY_SOURCE, tag=TAG_OK)
        print(f"[Processo {eu}] Recebi OK de {msg['remetente']}. Paro a minha tentativa.")
        
        return False
    
    else:
        # --- PASSO 3 ---
        # Se entrei aqui, significa que não há ninguém maior que eu vivo
        # (ou todos os maiores eram o 'morto').
        print(f"\n!!! [Processo {eu}] Sou o maior vivo! Viro COORDENADOR !!!\n")
        
        time.sleep(1) # Pausa para organização visual
        
        # Anuncia a vitória para todos os processos menores
        for i in range(total):
            if i != eu and i != morto:
                comm.send({'tipo': 'LIDER', 'id': eu}, dest=i, tag=TAG_LIDER)
        
        return True


# =============================================================================
# BLOCO 1: INTERFACE E CONFIGURAÇÃO
# =============================================================================
if my_rank == 0:
    print("="*50)
    print(f"Simulação Bully MPI - {num_procs} Processos")
    print("="*50)
    try:
        # O processo 0 age como interface com o usuário
        m = int(input("Quem sera o antigo coordenador (que vai morrer)? ID: "))
        i = int(input("Quem percebe a falha e inicia a eleicao? ID: "))
        config = {'morto': m, 'iniciador': i}
    except:
        sys.exit(0)

# =============================================================================
# BLOCO 2: SINCRONIZAÇÃO
# =============================================================================

# Broadcast: O processo 0 envia a variável 'config' para TODOS os outros processos.
# Antes dessa linha, só o Rank 0 sabia quem ia morrer. Depois dela, todos sabem.
config = comm.bcast(config, root=0)

proc_morto = config['morto']
proc_iniciador = config['iniciador']

# =============================================================================
# BLOCO 3: INÍCIO DO PROCESSO
# =============================================================================

# Se eu sou o processo designado para notar a falha, começo o efeito dominó.
if my_rank == proc_iniciador:
    print(f"[Processo {my_rank}] Percebi que {proc_morto} caiu. Iniciando eleição.")
    tentar_eleicao(my_rank, num_procs, proc_morto)

# =============================================================================
# BLOCO 4: LOOP DE ESCUTA
# =============================================================================
# Todos os processos (exceto o morto) ficam presos neste loop esperando mensagens.
# O loop só quebra quando um novo líder é anunciado.

lider_definido = False

while not lider_definido:
    # para e espera uma mensagem qualquer.
    msg = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
    
    # pega os dados da mensagem recebida
    tag = status.Get_tag()      # Qual o assunto?
    remetente = status.Get_source() # Quem mandou?

    # --- ALGUÉM MENOR QUER FAZER ELEIÇÃO ---
    if tag == TAG_ELEICAO:
        print(f"[Processo {my_rank}] Recebi ELEICAO de {remetente}.")
        
        # Regra do Valentão: Se alguém menor quer ser líder, eu (maior) digo:
        # "OK, fique quieto que eu sou maior que você, eu assumo a eleição".
        comm.send({'remetente': my_rank}, dest=remetente, tag=TAG_OK)
        
        # Agora que calei o menor, EU tento me eleger contra os meus superiores.
        tentar_eleicao(my_rank, num_procs, proc_morto)

    # --- ALGUÉM VENCEU A ELEIÇÃO ---
    elif tag == TAG_LIDER:
        novo_lider = msg['id']
        print(f"[Processo {my_rank}] Reconheço {novo_lider} como NOVO COORDENADOR.")
        
        # A eleição acabou, podemos sair do loop e encerrar o programa.
        lider_definido = True

    # --- RECEBI UM OK ---
    elif tag == TAG_OK:
        # ou fora de ordem, pois o tratamento principal do OK é feito dentro da função
        pass