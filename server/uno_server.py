import socket
import threading
import random
import time
from socket import *
import sys

#NUM_PLAYERS = sys.argv[1]
# Global current move
current_move = None


def server_client(connection_socket, ID):
    global current_move

    # Checa se é o dono da partida
    while (not game.started) and (game.player_turn != ID):
        time.sleep(0.5)

    while 1:

        while game.player_turn != ID:
            if not game.started:
                break
            time.sleep(0.5)

        print('Thread server_client waiting player ', ID, ' turn...')
        try:
            sentence = connection_socket.recv(1024)
        except Exception as msg:
            print("Caught exception: %s" % msg)
            break

        # No data receiving
        if sentence is None:
            print('No data receiving')
            continue

        # Byte -> String
        sentence = sentence.decode()
        if len(sentence.split(',')) < 3:
            connection_socket.send('Invalid syntax of uno protocol.'.encode())
            continue

        # START: 0,
        # BUY: 0,
        # PUT: BLUE 8 0
        #
        print(sentence)

        # Verifica procedencia dos comandos
        start, buy, put = sentence.split(',', 3)
        if len(put.split()) < 3:
            connection_socket.send('Invalid syntax of uno protocol.'.encode())
            continue
        garbage, colour, value, wild = put.split(None, 3)
        print('start: ', start)
        print('buy: ', buy)
        print('put: ', put)
        card = None
        if put != '0 0 0':
            if wild != '0':
                card = Card(colour=colour, wild=wild)
            else:
                card = Card(colour, value)
            code = 'put'
        elif start == '1':
            code = 'start'
        elif buy == '1':
            code = 'buy'
        else:
            code = 'exit'

        # Executa comandos
        if not game.started:
            if code == 'start':
                __game_started.acquire()
                game.started = True
                __game_started.release()
                print('Starting game...')

        elif code.lower() == 'exit':
            break

        __current_move_lock.acquire()

        current_move = (code, card)
        # print('Current move is: ', current_move)

        __current_move_lock.release()

        # Send back the process data
        mes = ''
        mes += 'ID ' + str(ID) + '/'
        mes += 'TURN ' + str(game.player_turn) + '/'
        mes += 'HAND ' + str(game.players[ID].get_hand()) + '/'
        mes += 'LAST ' + str(game.discards[-1].name)+'/'
        mes += 'PNUM ' + str(game.num_players) + '/'
        mes += 'PNUMC ' + str(game.att_ncards_players())
        print(mes)
        connection_socket.send(mes.encode())
        time.sleep(1.0)

    connection_socket.close()


def server():

    global current_move
    global game
    game = Game()

    server_port = 8888
    server_ip = "127.0.0.1"
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(4)
    server_socket.settimeout(30)

    sockets_connected = []
    threads_in_execution = []

    # Espera por players
    while (not game.started) and (game.num_players < 2):
        if game.num_players != 0:
            __game_started.release()
            print('Thread game release')

        print("Waiting for players, has current ", game.num_players, ' players...')
        client_socket, client_info = server_socket.accept()
        sockets_connected.append(client_socket)

        # Adiciona jogadores até o jogo começar
        game.add_player(Player(game.num_players, client_info[0], client_info[1]))

        print("Socket connected: ", client_info[-1])
        # Retorna o ID do jogador
        threads_in_execution.append(threading.Thread(target=server_client, args=(sockets_connected[-1], game.players[-1].id, )))
        threads_in_execution[-1].start()
        time.sleep(0.1)
        __game_started.acquire()
        print('Thread game acquired')

    __game_started.release()
    print('Thread game release')
    game.start()

    print('=== Game running ===')
    while game.started:
        __current_move_lock.acquire()
        if current_move is None:
            # print('Current move is: ', current_move)
            __current_move_lock.release()
            time.sleep(0.2)
        else:
            print('Current move is: ', current_move)
            game.play(current_move[0], current_move[1])
            current_move = None
            __current_move_lock.release()


class Game:
    def __init__(self):
        self.num_players = 0
        self.players = list()
        self.uno_deck = self.shuffle_deck(self.build_deck())
        self.discards = list()
        self.player_turn = 0
        self.play_direction = 1

        self.started = False
        self.max_players = 4
        self.draw_sum = 0

    def add_player(self, player):
        if self.num_players >= self.max_players:
            return False
        else:
            player.id = self.num_players
            self.players.append(player)
            self.num_players += 1
            return True

    def att_ncards_players(self):
        return [len(player.hand) for player in self.players]

    def build_deck(self):
        deck = list()
        colours = ['red', 'blue', 'green', 'yellow']
        values = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'draw_two', 'skip', 'reverse']
        wilds = ['wild', 'wild_draw_four']
        for colour in colours:
            for value in values:
                card = Card(colour, value)
                deck.append(card)
                if value != '0':
                    deck.append(card)
        for i in range(4):
            deck.append(Card(wild=wilds[0]))
            deck.append(Card(wild=wilds[1]))
        return deck

    def shuffle_deck(self, deck):
        for card_pos in range(len(deck)):
            rand_pos = random.randint(0, 107)
            deck[card_pos], deck[rand_pos] = deck[rand_pos], deck[card_pos]
        return deck

    def draw_cards(self, num_cards):
        cards_draw = list()
        for i in range(num_cards):
            cards_draw.append(self.uno_deck.pop())
        return cards_draw

    def discard_card(self, card):
        index_card = self.players[self.player_turn].hand.index(card)
        self.discards.append(card)
        del (self.players[self.player_turn].hand[index_card])

    def next_player_turn(self):
        last_card = self.discards[-1]
        if last_card.value is 'skip':
            next_player = self.player_turn + (2 * self.play_direction)
        else:
            next_player = self.player_turn + (1 * self.play_direction)

        if next_player < 0:
            next_player = next_player * -1
        elif next_player > (self.num_players - 1):
            next_player = (next_player % self.num_players)

        self.player_turn = next_player

    def can_play(self, card):
        last_colour = self.discards[-1].colour
        last_value = self.discards[-1].value

        if card.value == last_value or card.colour.lower() == last_colour.lower() or card.wild is not None:
            return True
        else:
            return False

    def start(self):
        print('Game started!')
        game.started = True
        self.discards.append(self.uno_deck.pop())
        while self.discards[-1].wild is not None or str(self.discards[-1].value).isalpha():
            self.discards.append(self.uno_deck.pop())

        print('First card is: ', self.discards[-1].colour, ' - ', self.discards[-1].value)

        for player in self.players:
            for i in range(7):
                player.hand.append(self.uno_deck.pop())

        print('Cards: ')
        for player in self.players:
            for card in player.hand:
                print('card of player[', player.ID, '] : ', card.colour, ' - ', card.value, ' - ',  card.wild)

    def play(self, move, card):
        print('Playing: ', move, ' - ', card.name)
        if move == 'buy':
            if self.draw_sum > 0:
                for i in range(self.draw_sum + 1):
                    self.players[self.player_turn].hand.append(self.uno_deck.pop())
                self.draw_sum = 0
            else:
                self.players[self.player_turn].hand.append(self.uno_deck.pop())

        elif move == 'put':
            if self.can_play(card) and self.players[self.player_turn].put_card(card):
                self.discards.append(card)
                if self.discards[-1].wild is not None:
                    if self.discards[-1].wild == 'wild_draw_four':
                        self.discards[-1].apply_effects()
                    self.discards.append(Card(card.colour, '--'))

                print('PLAYED!: ', card.colour, '-', card.value, '-', card.wild)
            else:
                print('Cannot play: ', card.colour, '-', card.value, '-', card.wild)
                return

        # Verifica vitoria
        if len(self.players[self.player_turn].hand) == 0:
            print(f'Player {self.player_turn} venceu!')
            self.started = False
            return

        # Faz o efeito da carta e vai para próximo jogador
        self.discards[-1].apply_effects()
        self.next_player_turn()
        print('Last placed card is: ', self.discards[-1].colour, ' - ', self.discards[-1].value, ' - ', self.discards[-1].wild)
        print('Player turn is: ', self.player_turn)
        print('Cards: ')
        for player in self.players:
            for att_card in player.hand:
                print('card of player[', player.ID, '] : ',  att_card.colour, ' - ',  att_card.value, ' - ',  att_card.wild)


class Player:
    def __init__(self, ID=None, IP=None, port=None):
        self.ID = ID
        self.IP = IP
        self.port = port
        self.hand = list()

    def get_hand(self):
        return [card.name for card in self.hand]

    def put_card(self, card):
        for actual_card in self.hand:
            if card.wild is not None:
                if actual_card.wild == card.wild:
                    self.hand.remove(actual_card)
                    return True
            if actual_card.colour == card.colour.lower() and actual_card.value == card.value:
                self.hand.remove(actual_card)
                return True
        else:
            return False


class Card:
    def __init__(self, colour=None, value=None, wild=None):
        self.colour = colour
        self.value = value
        self.wild = wild
        if wild is None:
            self.name = self.colour+'_'+self.value
        else:
            self.name = self.wild
        if value == 'reverse' or value == 'skip' or wild is not None:
            self.effect = True
        else:
            self.effect = False

    def apply_effects(self):
        if self.effect:
            if self.value == 'reverse':
                game.play_direction *= -1
            elif self.value == 'skip':
                # Done in game.next_player_turn()
                pass
            elif self.wild in 'wild_draw_four':
                game.draw_sum += 4
                print('Draw_sum: ', game.draw_sum)
            elif 'draw_two' == self.value:
                game.draw_sum += 2
                print('Draw_sum: ', game.draw_sum)


if __name__ == '__main__':
    game = Game()
    __current_move_lock = threading.Lock()
    __game_started = threading.Lock()
    server()
