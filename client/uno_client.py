from socket import *
import threading
import sys
import pygame
import operator
import re

SERVER_IP = sys.argv[1]
SERVER_PORT = int(sys.argv[2])

# Iniciando config da GUI
pygame.init()
size = width, height = 1200, 720
black = 0, 0, 0
screen = pygame.display.set_mode(size)

colors = ['blue_', 'red_', 'yellow_', 'green_']
path = "images/"
extension = ".png"


# CONSTANTES
global MESSAGE
global PLAYER_ID
global PLAYER_TURN
global PLAYERS_NUM
global P_NUM_CARDS
global LAST_DISCARD
global PLAYER_HAND
global ERR
deck = dict()
PLAYER_ID = None
PLAYER_TURN = 0
PLAYERS_NUM = 2
P_NUM_CARDS = [2, 4]
LAST_DISCARD = 'red_6'
PLAYER_HAND = ['red_7']
ERR = None
MESSAGE = 'INIT'
# PROTOCOLO
def update_consts(res):
    print(res)
    res2 = res.split('/')
    print(res2)
    res3 = [x.split(' ', 1)[1] for x in res2]
    PLAYER_ID, PLAYER_TURN, PLAYER_HAND, LAST_DISCARD, PLAYERS_NUM, P_NUM_CARDS  = res3
    eval(PLAYER_TURN)
    eval(PLAYER_HAND)
    eval(P_NUM_CARDS)
    print(PLAYER_ID)


def server_output(client_socket):
    while 1:
        att = client_socket.recv(1500)

        print(update_consts(att.decode()))


def client_input(client_socket):
    while 1:
        message = input('Enter the message: ')
        client_socket.send(message.encode())
        pass


def client():
    server_name = SERVER_IP
    server_port = SERVER_PORT

    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((server_name, server_port))

    server_output_thread = threading.Thread(target=server_output, args=(client_socket, ))
    server_output_thread.start()

    client_input_thread = threading.Thread(target=client_input, args=(client_socket, ))
    client_input_thread.start()


class Card:
    def __init__(self, color=0, number=0, image_front=None, x=0, y=0, wild=None):
        self.color = color
        self.number = number
        self.wild = wild
        self.image = image_front
        if number is not None:
            self.name = str(color) + str(number)
        else:
            self.name = wild
        self.x = x
        self.y = y
        self.width = 130
        self.height = 182
        self.pos = self.image.get_rect(x=x, y=y)

    def click(self, pos):
        x1 = pos[0]
        y1 = pos[1]
        if self.color == 'deck':
            var_width = 130
        else:
            var_width = 80
        if self.x <= x1 <= self.x + var_width and self.y <= y1 <= self.y + self.height:
            return True
        else:
            return False

    def req(self, colour_wild_choice):
        if self.number is not None:
            m = f'START: 0, BUY: 0, PUT: {self.color} {self.number} 0'
        elif self.wild is not None:
            m = f'START: 0, BUY: 0, PUT: {self.colour_wild_choice} 0 {self.wild}'

        else:
            print(f'Movimento inválido')


class Button:
    def __init__(self, text, x, y, color):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.width = 50
        self.height = 30

    def draw(self, win):
        pygame.draw.rect(win, self.color, (self.x, self.y, self.width, self.height))
        font = pygame.font.SysFont("comicsans", 40)
        text = font.render(self.text, 1, (255,255,255))
        win.blit(text, (self.x + round(self.width/2) - round(text.get_width()/2), self.y + round(self.height/2) - round(text.get_height()/2)))

    def click(self, pos):
        x1 = pos[0]
        y1 = pos[1]
        if self.x <= x1 <= self.x + self.width and self.y <= y1 <= self.y + self.height:
            return True
        else:
            return False


values = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'draw_two', 'skip', 'reverse']
wilds = ['wild', 'wild_draw_four']
for color in colors:
    for value in values:
        c_name = str(color+value)
        full_path = path + str(color) + str(value) + extension
        deck[c_name]=(Card(color, value, pygame.image.load(full_path)))
full_path = path + 'wild' + extension
deck['wild']=(Card(image_front=pygame.image.load(full_path),wild=wilds[0]))
full_path = path + 'wild_draw_four' + extension
deck['wild_draw_four']=(Card(image_front=pygame.image.load(full_path),wild=wilds[1]))
PLAYER_HAND = [k for k in deck]
deck_card_image = pygame.image.load("images/card_back.png")
deck_draw = Card('deck', 666, deck_card_image, x=670, y=249)
btns = [Button("Play", 575, 307, (0, 0, 0)), Button("Skip", 575, 357, (255, 0, 0))]
i = 0
for card in PLAYER_HAND:
    deck.get(card).x = i * 80
    deck.get(card).y = 537
    i += 1
    deck.get(card).pos = deck.get(card).image.get_rect(x=deck.get(card).x, y=deck.get(card).y)
deck.get(LAST_DISCARD).pos.update((400, 249), [130, 182])

def main():
    run = True
    client()
    print("You are player", PLAYER_ID)

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
                run = False
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            if deck.get(PLAYER_HAND[-1]).x >= 1200:
                for card in PLAYER_HAND:
                    deck.get(card).x -= 80
                    deck.get(card).pos.update(tuple(map(operator.sub, (deck.get(card).x, 537), (0, 0))), [130, 182])
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            if deck[PLAYER_HAND[0]].x < 0:
                for card in PLAYER_HAND:
                    deck.get(card).x += 80
                    deck.get(card).pos.update(tuple(map(operator.sub, (deck.get(card).x, 537), (0, 0))), [130, 182])
        if PLAYER_ID == PLAYER_TURN:
            if pygame.mouse.get_pressed(3)[0]:
                if deck_draw.click(pygame.mouse.get_pos()):
                    deck_draw.req()
                for card in PLAYER_HAND:
                    if deck.get(card).click(pygame.mouse.get_pos()):
                        deck.get(card).req()

        screen.fill(black)

        screen.blit(deck_draw.image, deck_draw.pos)
        screen.blit(deck.get(LAST_DISCARD).image, deck.get(LAST_DISCARD).pos)
        for card in PLAYER_HAND:
            screen.blit(deck.get(card).image, deck.get(card).pos)
        for btn in btns:
            btn.draw(screen)

        pygame.display.flip()


def menu_screen():
    run = True

    while run:
        screen.fill((128, 128, 128))
        font = pygame.font.SysFont('comicsans', 60)
        text = font.render('UNO'
                           'Click to play', 1, (0,0,0))
        screen.blit(text, (550, 340))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                run = False
    print(f'Abrindo a main')
    main()

main()

