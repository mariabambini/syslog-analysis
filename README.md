# syslog-analysis
Simulação de ambiente real para teste de viabilidade de uso de modelo de análise de logs em instituição de ensino para detecção de anomalias em máquinas de laboratório.

(descrição do que tem)

## Instalação

1. O primeiro passo é verificar se o GNS3 e Docker estão instalados e funcionando.

Verificar se o GNS3 está instalado

```console
$ gns3
```
Verificar se o Docker está instalado

```console
$ docker --version
```

Verificar se o Docker está rodando

```console
$ docker ps
```

2. Feito isso, integrar o Docker ao GNS3.
2.1 No GNS3, vá em Edit -> Preferences -> Server. Confirme que 'Enable the local server' está marcado, 'Host: localhost', 'Port: 3080 TCP'.

2.2 Importar a imagem do container (vou utilizar Ubuntu 22.04)
Docker -> Docker containers -> New -> New image. 'Image name: ubuntu:22.04'. 'Network adapters: 1'.  

Caso tenha erro de permissão:

```console
sudo usermod -aG docker $USER
```

