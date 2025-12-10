# Vamos começar
Primeira coisa é que você deve ter uma versão do python instalada, usei a versão 3.13.3

# Instalação
Agora com o python instalado precisamos de um lugar para trabalhar, usaremos o VS code para isso, então, vamos começar.
Abrindo o terminal na sua pasta do projeto vamos rodar os seguintes comandos:
- Criar nosso ambiente virtual:
```
python -m venv venv
```
- Acessar o script (caso não esteja ativado scripts, veja como ativar aqui Windows: https://www.youtube.com/watch?v=mmXzYxR7s9c)
```
./venv/bin/Activate.ps1
```
- Instalar a dependência do projeto para uso do MIP
```
pip install mpi4py
```
# Rodar o projeto
- O comando para iniciar o arquivo (tenha o executável do mpi instalado na máquina) é:
```
mpiexec -n 10 python .\valentao-mpi.py
```
O 10 representa o número de atores que irão fazer o processo de eleição quando o antigo falhar.

Após rodar irá indicar no terminal conforme solicitado quem é o antigo coordenador que ficou offline e quem irá iniciar a nova eleição.