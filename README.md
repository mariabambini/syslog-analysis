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
2.1 No GNS3, vá em Edit -> Preferences -> GNS3 Server -> Local Server. Confirme que 'Enable the local server' está marcado, 'Host: 127.0.0.1', 'Port: 3080'.

2.2 Agora verificar o suporte ao Docker:
Docker -> Docker containers. 'Docker support' deve estar enabled, 'Server:local' (a variar se não estiver usando backend local).

2.3 Importar a imagem do container (vou utilizar Ubuntu 22.04)
(Ainda em Docker -> Docker containers) New -> New image. 'Image name: ubuntu:22.04'.

