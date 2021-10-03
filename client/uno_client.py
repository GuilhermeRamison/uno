from socket import *
import threading
import sys
import pygame
import operator
import time
import json

if len(sys.argv) > 1:
    SERVER_IP = sys.argv[1]
    SERVER_PORT = int(sys.argv[2])
else:
    SERVER_IP = '127.0.0.1'
    SERVER_PORT = 8888


# CONSTANTS
MESSAGE = 'INIT'
NEW_MESSAGE = False
PLAYER_ID = None
PLAYER_TURN = None
PLAYERS_NUM = None
P_NUM_CARDS = None
LAST_DISCARD = None
PLAYER_HAND = []
DRAW_SUM = 0
ERR = None
MAX_PLAYERS = 2


# PROTOCOL
def update_consts(res):
    # update antigo
    '''print(res)
    res2 = res.split('/')
    print(res2)
    res3 = [x.split(' ', 1)[1] for x in res2]
    global PLAYER_ID, PLAYER_TURN, PLAYER_HAND, LAST_DISCARD, PLAYERS_NUM, P_NUM_CARDS
    PLAYER_ID, PLAYER_TURN, PLAYER_HAND, LAST_DISCARD, PLAYERS_NUM, P_NUM_CARDS = res3
    eval(PLAYER_ID)
    eval(PLAYER_TURN)
    eval(PLAYER_HAND)
    #eval(LAST_DISCARD)
    eval(PLAYERS_NUM)
    eval(P_NUM_CARDS)'''
    # update novo
    global PLAYER_ID, PLAYER_TURN, PLAYER_HAND, LAST_DISCARD, PLAYERS_NUM, P_NUM_CARDS,DRAW_SUM, MAX_PLAYERS
    res_dict = json.loads(res)
    if 'ID' in res_dict:
        PLAYER_ID = res_dict.get('ID')
    if 'HAND' in res_dict:
        PLAYER_HAND = res_dict.get('HAND')
    if 'LAST' in res_dict:
        LAST_DISCARD = res_dict.get('LAST')
    PLAYER_TURN = res_dict.get('TURN')
    PLAYERS_NUM = res_dict.get('PNUM')
    P_NUM_CARDS = res_dict.get('PNUMC')
    DRAW_SUM = res_dict.get('DRS')
    MAX_PLAYERS = res_dict.get('MAX')


def server_output(client_socket):
    while 1:
        att = client_socket.recv(1500)
        att = att.decode()
        print(f'Server response: {att}')
        if len(att) > 0:
            if '}{' in att:
                att2 = att.split('}{')
            update_consts(att)


def client_input(client_socket):
    global NEW_MESSAGE, MESSAGE
    while 1:
        if NEW_MESSAGE:
            print(MESSAGE)
            client_socket.send(MESSAGE.encode())
            NEW_MESSAGE = False
            time.sleep(0.1)


def req(card, skip=False):
    global NEW_MESSAGE, MESSAGE
    if skip:
        MESSAGE = f'SKIP: 1, BUY: 0, PUT: 0 0 0'
    elif card.number == 666 or card.color == 'deck':
        MESSAGE = f'SKIP: 0, BUY: 1, PUT: 0 0 0'
    elif card.number is not None:
        MESSAGE = f'SKIP: 0, BUY: 0, PUT: {card.color} {card.number} 0'
    elif card.wild is not None:
        MESSAGE = f'SKIP: 0, BUY: 0, PUT: {card.color} 0 {card.wild}'
    NEW_MESSAGE = True


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
    def __init__(self, color=None, number=None, image_front=None, x=0, y=0, wild=None):
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


class Button:
    def __init__(self, text, x, y, color=(0, 0, 0), width=160, height=30, p_id=0, upd_color=True, is_rect=True, tam=25):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.width = width
        self.height = height
        self.p_id = p_id
        self.is_rect = is_rect
        self.upd_color = upd_color
        self.tam = tam

    def draw(self, win):
        global PLAYER_TURN
        if PLAYER_TURN == self.p_id and self.upd_color:
            color = (255,0,0)
        else:
            color = self.color
        if self.is_rect:
            pygame.draw.rect(win, color, (self.x, self.y, self.width, self.height))
        else:
            pygame.draw.circle(screen, (255, 0, 0), (600, 360), 60)
        font = pygame.font.SysFont("comicsans", self.tam)
        text = font.render(self.text, 1, (255,255,255))
        win.blit(text, (self.x + round(self.width/2) - round(text.get_width()/2), self.y + round(self.height/2) - round(text.get_height()/2)))

    def click(self, pos):
        x1 = pos[0]
        y1 = pos[1]
        if self.x <= x1 <= self.x + self.width and self.y <= y1 <= self.y + self.height:
            return True
        else:
            return False


# Iniciando config da GUI
pygame.init()
size = width, height = 1200, 720
black = 0, 0, 0
screen = pygame.display.set_mode(size)
colors = ['blue_', 'red_', 'yellow_', 'green_']
path = "images/"
extension = ".png"
values = ['', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'draw_two', 'skip', 'reverse']
deck = dict()
for color in colors:
    for value in values:
        c_name = str(color + value)
        full_path = path + str(color) + str(value) + extension
        deck[c_name] = (Card(color, value, pygame.image.load(full_path)))
        if value != 0:
            c_name = str(color + '_' + value)
            full_path = path + str(color) + str(value) + extension
            deck[c_name] = (Card(color+'_', value, pygame.image.load(full_path)))
full_path = path + 'wild' + extension
for i in range(4):
    deck['wild_'+str(i)] = (Card(image_front=pygame.image.load(full_path), wild='wild_'+str(i)))
full_path = path + 'wild_draw_four' + extension
for i in range(4):
    deck['wild_draw_four_'+str(i)] = (Card(image_front=pygame.image.load(full_path), wild='wild_draw_four_'+str(i)))
deck_card_image = pygame.image.load("images/card_back.png")
deck_draw = Card('deck', 666, deck_card_image, x=670, y=249)
cards_p_image1 = pygame.image.load("images/card_back_alt1.png")
cards_p_image2 = pygame.image.load("images/card_back_alt2.png")
cards_p_image3 = pygame.image.load("images/card_back_alt3.png")
card_p1 = Card('card_p1', None, cards_p_image1, x=535, y=0)
card_p2 = Card('card_p2', None, cards_p_image2, x=0, y=295)
card_p3 = Card('card_p3', None, cards_p_image3, x=1017, y=295)
draw_count = Button("+0", 535, 300, (255, 0, 0), width=120, height=120,  is_rect=False, tam=50)
pos_0 = Button("Player 0 || 7 Cards", 520, 500, (0, 0, 0), p_id=0)
pos_1 = Button("Player 1 || 7 Cards", 520, 190, (0, 0, 0), p_id=1)
pos_2 = Button("Player 2 || 7 Cards", 20, 260, (0, 0, 0), p_id=2)
pos_3 = Button("Player 3 || 7 Cards", 1020, 260, (0, 0, 0), p_id=3)
pos_btns = [pos_0, pos_1, pos_2, pos_3]


def def_pos_info(btns):
    global PLAYER_ID, P_NUM_CARDS, MAX_PLAYERS
    if btns is not None and len(P_NUM_CARDS) == MAX_PLAYERS:
        if PLAYER_ID == 0:
            btns[0].text = f'Player {PLAYER_ID} || {P_NUM_CARDS[PLAYER_ID]} Cards'
            btns[0].p_id = 0
            btns[1].text = f'Player 1 || {P_NUM_CARDS[1]} Cards'
            btns[1].p_id = 1
            if MAX_PLAYERS >= 3:
                btns[2].text = f'Player 2 || {P_NUM_CARDS[2]} Cards'
                btns[2].p_id = 2
            if MAX_PLAYERS >= 4:
                btns[3].text = f'Player 3 || {P_NUM_CARDS[3]} Cards'
                btns[3].p_id = 3
        elif PLAYER_ID == 1:
            print(btns[0].text)
            print(P_NUM_CARDS[PLAYER_ID])
            btns[0].text = f'Player {PLAYER_ID} || {P_NUM_CARDS[PLAYER_ID]} Cards'
            btns[0].p_id = 1
            btns[1].text = f'Player 0 || {P_NUM_CARDS[0]} Cards'
            btns[1].p_id = 0
            if MAX_PLAYERS >= 3:
                btns[2].text = f'Player 2 || {P_NUM_CARDS[2]} Cards'
                btns[2].p_id = 2
            if MAX_PLAYERS >= 4:
                btns[3].text = f'Player 3 || {P_NUM_CARDS[3]} Cards'
                btns[3].p_id = 3
        elif PLAYER_ID == 2:
            btns[0].text = f'Player {PLAYER_ID} || {P_NUM_CARDS[PLAYER_ID]} Cards'
            btns[0].p_id = 2
            btns[1].text = f'Player 0 || {P_NUM_CARDS[0]} Cards'
            btns[1].p_id = 0
            if MAX_PLAYERS >= 3:
                btns[2].text = f'Player 1 || {P_NUM_CARDS[1]} Cards'
                btns[2].p_id = 1
            if MAX_PLAYERS >= 4:
                btns[3].text = f'Player 3 || {P_NUM_CARDS[3]} Cards'
                btns[3].p_id = 3
        elif PLAYER_ID == 3:
            btns[0].text = f'Player {PLAYER_ID} || {P_NUM_CARDS[PLAYER_ID]} Cards'
            btns[0].p_id = 3
            btns[1].text = f'Player 1 || {P_NUM_CARDS[1]} Cards'
            btns[1].p_id = 1
            if MAX_PLAYERS >= 3:
                btns[2].text = f'Player 0 || {P_NUM_CARDS[0]} Cards'
                btns[2].p_id = 0
            if MAX_PLAYERS >= 4:
                btns[3].text = f'Player 2 || {P_NUM_CARDS[2]} Cards'
                btns[3].p_id = 2


def winner():
    global P_NUM_CARDS
    P_NUM_CARDS = []
    for n in P_NUM_CARDS:
        if n == 0:
            return P_NUM_CARDS.index(n)
    return -1


def winner_screen():
    run = True
    color_menu = pygame.display.set_mode(size)
    while run:
        p_win = Button(f'Player {PLAYER_ID} win!', 575, 357, (255, 0, 0), tam=60)
        p_win.draw(color_menu)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                run = False


def game():
    run = True
    title = 'UNO - Player '+ str(PLAYER_ID)
    pygame.display.set_caption(title)
    while len(PLAYER_HAND) == 0:
        time.sleep(0.5)
    while run:
        for event in pygame.event.get():
            if PLAYER_ID == PLAYER_TURN:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if deck_draw.click(pygame.mouse.get_pos()):
                        req(deck_draw)
                    else:
                        for card in PLAYER_HAND:
                            if deck.get(card).click(pygame.mouse.get_pos()):
                                if deck.get(card).wild is not None:
                                    color_choice(deck.get(card))
                                req(deck.get(card))
            if event.type == pygame.QUIT:
                sys.exit()
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
        if winner() != -1:
            winner_screen()
            run = False

        deck.get(LAST_DISCARD).pos.update((400, 249), [130, 182])
        i = 0
        for card in PLAYER_HAND:
            deck.get(card).x = i * 80
            deck.get(card).y = 537
            i += 1
            deck.get(card).pos = deck.get(card).image.get_rect(x=deck.get(card).x, y=deck.get(card).y)
        screen.fill(black)
        screen.blit(deck_draw.image, deck_draw.pos)
        screen.blit(deck.get(LAST_DISCARD).image, deck.get(LAST_DISCARD).pos)
        for card in PLAYER_HAND:
            screen.blit(deck.get(card).image, deck.get(card).pos)
        draw_count.text = f'+{DRAW_SUM}'
        draw_count.draw(screen)
        def_pos_info(pos_btns)
        if PLAYERS_NUM >= 2:
            screen.blit(card_p1.image, card_p1.pos)
            pos_0.draw(screen)
            pos_1.draw(screen)
        if PLAYERS_NUM >= 3:
            screen.blit(card_p2.image, card_p2.pos)
            pos_2.draw(screen)
        if PLAYERS_NUM == 4:
            screen.blit(card_p3.image, card_p3.pos)
            pos_3.draw(screen)
        pygame.display.flip()

def color_choice(card):
    run = True
    color_menu = pygame.display.set_mode(size)
    blue_btn = Button("", 500, 270, (0,195,229), width=100, height=100, upd_color=False)
    red_btn = Button("", 500, 370, (245,100,98), width=100, height=100, upd_color=False)
    yellow_btn = Button("", 600, 270, (247,227,89), width=100, height=100, upd_color=False)
    green_btn = Button("", 600, 370, (47,226,155), width=100, height=100, upd_color=False)
    while run:
        blue_btn.draw(color_menu)
        red_btn.draw(color_menu)
        yellow_btn.draw(color_menu)
        green_btn.draw(color_menu)
        font = pygame.font.SysFont('comicsans', 60)
        text = font.render(f'Choice a color:', True, (255, 255, 255))
        screen.blit(text, (500, 220))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if blue_btn.click(pygame.mouse.get_pos()):
                    card.color = 'blue_'
                elif red_btn.click(pygame.mouse.get_pos()):
                    card.color = 'red_'
                elif yellow_btn.click(pygame.mouse.get_pos()):
                    card.color = 'yellow_'
                elif green_btn.click(pygame.mouse.get_pos()):
                    card.color = 'green_'
                run = False


def menu():
    global PLAYERS_NUM, MAX_PLAYERS
    run = True
    while run:
        screen.fill((128, 128, 128))
        font = pygame.font.SysFont('comicsans', 60)
        text = font.render(f'Waiting players...', True, (0,0,0))
        status = font.render(f'({PLAYERS_NUM}/{MAX_PLAYERS})', 1, (0, 0, 0))
        screen.blit(text, (450, 300))
        screen.blit(status, (550, 340))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                run = False
        if PLAYERS_NUM == MAX_PLAYERS:
            print('JANELA DO GAME')
            game()


client()
time.sleep(0.5)
menu()
