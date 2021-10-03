# UNO GAME
O jogo foi desenvolvido como um projeto para a disciplina de Redes de Computadores.
O propósito é fazer uma aplicação usando os conceitos aprendidos em aula. O jogo tem um modelo Cliente-Servidor e utiliza TCP como protocolo de transporte.  

- Guilherme Ramison [gramison@inf.ufpel.edu.br]
- Lucas Zanusso Morais [lzmorais@inf.ufpel.edu.br]

## Executando o jogo
1.Clone o repositório e instale as dependências
````buildoutcfg
pip install -r requirements.txt
````
2.Da pasta raiz, vá para _server_ e execute _uno_server.py_
````buildoutcfg
cd server 
````
######Parâmetros _uno_server.py_ <NUM_PLAYERS> <IP> <PORT>
````buildoutcfg
python uno_server.py 2 127.0.0.1 8888
````
###### Se não passar os argumentos, o _default_ é <2> <127.0.0.1> <8888>
3.Da pasta raiz, vá para _client_ e execute _uno_client.py_
````buildoutcfg
cd client
````
######Parâmetros _uno_client.py_ <IP> <PORTA>
`````buildoutcfg
python uno_client.py 127.0.0.1 8888
`````
###### Se não passar os argumentos, o _default_ é <127.0.0.1> <8888>