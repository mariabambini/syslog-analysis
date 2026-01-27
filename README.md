# syslog-analysis
Simulação de ambiente real para teste de viabilidade de uso de modelo de análise de logs em instituição de ensino para detecção de anomalias em máquinas de laboratório.

(descrição)

## Dependências
* xterm
* dynamips

## Instalação

1. O primeiro passo é verificar se o GNS3 e Docker estão instalados e funcionando.

Verificar se o GNS3 está instalado

```console
gns3
```
Verificar se o Docker está instalado

```console
docker --version
```

Verificar se o Docker está rodando

```console
docker ps
```

2. Feito isso, integrar o Docker ao GNS3
No GNS3, vá em Edit → Preferences → Server. 
* Confirme que 'Enable the local server' está marcado. 
* Host: localhost
* Port: 3080 TCP

Importar a imagem do container (vou utilizar Ubuntu 22.04)
Docker → Docker containers → New → New image. 
* Image name: ubuntu:22.04
* Name: cliente
* Network adapters: 1
* Start command: /bin/bash
* Console type: telnet
* Environment: vazio

Caso tenha erro de permissão:

```console
sudo usermod -aG docker $USER
```
Feito isso, o container deve aparecer como na imagem:

| <img src="img/container.jpeg" alt="image" width="60%" height="auto"> |
|:--:|
| Figura 1 - Container Docker Ubuntu |

Para testar, arrasta uma máquina Ubuntu para o projeto e clique em Start.

Faça os mesmos passos para criar uma máquina servidor. 

## Configurar rede local

1. Utilize um ethernet switch para conectar as duas máquinas.
Tente iniciar os dispositivos para ter certeza que não houve nenhum erro.

2. Configure os IPs.

* Máquina cliente:
```console
ip addr add 192.168.10.10/24 dev eth0
ip link set eth0 up
```
* Máquina servidor:
```console
ip addr add 192.168.10.20/24 dev eth0
ip link set eth0 up
```

Tente pingar as máquinas para garantir que tudo ocorreu certo.
