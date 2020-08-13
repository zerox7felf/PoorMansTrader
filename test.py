#!/bin/env python
import json
import pdb
import math
import trader

import pygame
from pygame.locals import *

from datetime import datetime
from binance.client import Client

### OPEN API ###
api_fp = open("api_key.json", "r")
api_keys = json.load(api_fp)
api_fp.close()

### CONSTRANTS ###
width = 1024
height = 800

SHOW_HIGHPOINTS = False
SHOW_LOWPOINTS = False
SHOW_BUYPOINTS = True
SHOW_SELLPOINTS = True
smoothness = 32

### HELPER FUNCTIONS ###

def get_kline(kline):
    return {
        "open_time":kline[0], "close_time":kline[6], "open":float(kline[1]),
        "high":float(kline[2]), "low":float(kline[3]), "close":float(kline[4]),
        "middle":(float(kline[1])+float(kline[4]))/2
    }

# x =           x position on screen
# w =           width of bar
# floor_val =   lowest value at bottom of screen
# ceil_val  =   highest value at top of screen
def draw_kline(screen, kline, x, w, floor_val, ceil_val):
    span_to_show = ceil_val - floor_val
    y = height - (kline["high"] - floor_val) * (height / span_to_show)
    h = (kline["high"] - kline["low"]) * (height / span_to_show)
    screen.fill((100,100,100), (int(x), int(y), int(w), int(h)))

    y = height - (max(kline["open"], kline["close"]) - floor_val) * (height / span_to_show)
    h = (abs(kline["open"] - kline["close"])) * (height / span_to_show)
    screen.fill((200,25,25) if kline["close"] < kline["open"] else (25,200,25), (int(x), int(y), int(w), int(h)))

### MAIN LOOP ###

pygame.init()
screen = pygame.display.set_mode((width,height))
font = pygame.font.Font(None, 15)

client = Client(api_keys["api_key"], api_keys["api_secret"])
print("Getting klines...")
symbol = "BTCUSDT"
full_klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, "6 hours ago UTC")
processed_klines = []
for kline in full_klines:
    processed_klines.append(get_kline(kline))
print("Done")

print("Generating averages...")
smoothed_klines = []
#smoothness = 16 # Moved to constants
for i in range(smoothness, len(full_klines)):
    #avg_value = (get_kline(full_klines[i])["middle"] + get_kline(full_klines[i-1])["middle"] + get_kline(full_klines[i-2])["middle"])/3

    avg_value = 0
    for j in range(smoothness+1):
        avg_value += get_kline(full_klines[i-j])["middle"]

    avg_value = avg_value/(smoothness+1)
    smoothed_klines.append({"middle":avg_value})

print("Done")

floor_val = get_kline(full_klines[0])["low"] - 200 if get_kline(full_klines[0])["low"] > 200 else 1
ceil_val = get_kline(full_klines[0])["high"] + 200
leftmost_val = 0
rightmost_val = len(full_klines)

trade_algo = trader.TwoPointTerry()
trade_algo2 = trader.TittyToucher(smoothness) # 16 seems to work ok
trade_algo2_avgs = []
trade_below_avg_positions = []
trade_above_avg_positions = []
trade_pos = 0
trade_bought_positions = []
trade_sold_positions = []
trade_highpoint_positions = []
trade_lowpoint_positions = []
trade_downward_slope_positions = []
trade_upward_slope_positions = []

trade_done = False

while True:
    ### DRAW ###
    screen.fill((0,0,0))

    x = 0
    last_kline = None
    klines = full_klines[leftmost_val:rightmost_val]
    for kline in klines:
        draw_kline(screen, get_kline(kline), x, width/len(klines)-1, floor_val, ceil_val)
        if last_kline != None:
            pygame.draw.line(
                screen, (255,0,255),
                (
                    int(x - width/len(klines)/2),
                    int(height - (last_kline["middle"] - floor_val) * (height / (ceil_val - floor_val)))
                ),
                (
                    int(x + width/len(klines)/2),
                    int(height - (get_kline(kline)["middle"] - floor_val) * (height / (ceil_val - floor_val)))
                ),
                2
            )
        last_kline = get_kline(kline)
        x += width/len(klines)

    last_val = smoothed_klines[leftmost_val]["middle"]
    for x in range(leftmost_val,min(rightmost_val,len(smoothed_klines))):
        pygame.draw.line(
            screen, (255,255,255),
            (
                int((x-leftmost_val+smoothness-1)*width/len(klines)),
                int(height - (last_val - floor_val) * (height / (ceil_val - floor_val)))
            ),
            (
                int((x-leftmost_val+smoothness)*width/len(klines)),
                int(height - (smoothed_klines[x]["middle"] - floor_val) * (height / (ceil_val - floor_val)))
            ),
            2
        )
        last_val = smoothed_klines[x]["middle"]

    x = 0
    last_val = 0
    for y in trade_algo2_avgs:
        pygame.draw.line(
            screen, (150,150,150),
            (
                int((x-leftmost_val-1)*width/len(klines)),
                int(height - (last_val - floor_val) * (height / (ceil_val - floor_val)))
            ),
            (
                int((x-leftmost_val)*width/len(klines)),
                int(height - (y - floor_val) * (height / (ceil_val - floor_val)))
            ),
            2
        )
        last_val = y
        x+=1

    if SHOW_BUYPOINTS:
        for bought_position in trade_bought_positions:
            pygame.draw.line(
                screen, (00,255,0),
                (int((bought_position-leftmost_val)*width/len(klines)), 0),
                (int((bought_position-leftmost_val)*width/len(klines)), height),
                1
            )

    if SHOW_SELLPOINTS:
        for sold_position in trade_sold_positions:
            pygame.draw.line(
                screen, (255,0,0),
                (int((sold_position-leftmost_val)*width/len(klines)), 0),
                (int((sold_position-leftmost_val)*width/len(klines)), height),
                1
            )

    if SHOW_HIGHPOINTS:
        for highpoint_position in trade_highpoint_positions:
            pygame.draw.line(
                screen, (255,255,0),
                (int((highpoint_position-leftmost_val)*width/len(klines)), 0),
                (int((highpoint_position-leftmost_val)*width/len(klines)), height),
                1
            )

    if SHOW_LOWPOINTS:
        for lowpoint_position in trade_lowpoint_positions:
            pygame.draw.line(
                screen, (0,0,255),
                (int((lowpoint_position-leftmost_val)*width/len(klines)), 0),
                (int((lowpoint_position-leftmost_val)*width/len(klines)), height),
                1
            )

    for slope_position in trade_downward_slope_positions:
        screen.fill(
            (255,0,0),
            (
                int((slope_position-leftmost_val)*width/len(klines)), height-5,
                int(width/len(klines))-1, 5
            )
        )

    for above_position in trade_above_avg_positions:
        screen.fill(
            (0,255,0),
            (
                int((above_position-leftmost_val)*width/len(klines)), height-10,
                int(width/len(klines))-1, 5
            )
        )

    for below_position in trade_below_avg_positions:
        screen.fill(
            (0,0,255),
            (
                int((below_position-leftmost_val)*width/len(klines)), height-10,
                int(width/len(klines))-1, 5
            )
        )

    for slope_position in trade_upward_slope_positions:
        screen.fill(
            (0,255,0),
            (
                int((slope_position-leftmost_val)*width/len(klines)), height-5,
                int(width/len(klines))-1, 5
            )
        )

    text = font.render(str(ceil_val), 1, (255, 255, 255))
    screen.blit(text, (width-50, 0))
    text = font.render(str(floor_val), 1, (255, 255, 255))
    screen.blit(text, (width-50, height-15))
    text = font.render(symbol, 1, (255, 255, 255))
    screen.blit(text, (0,0))

    mouse_pos = pygame.mouse.get_pos()
    pygame.draw.line(screen, (50,50,50), (mouse_pos[0],0), (mouse_pos[0],height))
    pygame.draw.line(screen, (50,50,50), (0,mouse_pos[1]), (width,mouse_pos[1]))
    text = font.render(str(((height-mouse_pos[1])/height) * (ceil_val-floor_val)+floor_val), 1, (255, 255, 255))
    screen.blit(text, (0,mouse_pos[1]-15))

    pygame.display.flip()

    ### UPDATE ###
    for event in pygame.event.get():
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 4:
                if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                    leftmost_val += 1
                    rightmost_val -= 1
                else:
                    leftmost_val -= 1
                    rightmost_val -= 1
            elif event.button == 5:
                if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                    leftmost_val -= 1
                    rightmost_val += 1
                else:
                    leftmost_val += 1
                    rightmost_val += 1

    if leftmost_val < 0:
        leftmost_val = 0
    if rightmost_val > len(full_klines):
        rightmost_val = len(full_klines)

    movement = pygame.mouse.get_rel()
    if movement[1] != 0:
        span = ceil_val - floor_val
        if pygame.mouse.get_pressed()[0]:
            floor_val += (movement[1]/height) * span
            ceil_val += (movement[1]/height) * span
        elif pygame.mouse.get_pressed()[1]:
            floor_val -= (movement[1]/height) * span
            ceil_val += (movement[1]/height) * span

        if floor_val < 1:
            floor_val = 1
        if ceil_val < 5:
            ceil_val = 5
        if ceil_val < floor_val:
            floor_val = ceil_val - 1

    ### PRICES ###
    if trade_pos < len(full_klines):
        trade_algo.process(processed_klines[:trade_pos+1])
        trade_algo2_avgs.append(trade_algo2.process(processed_klines[:trade_pos+1]))
        state = trade_algo.get_state()
        state2 = trade_algo2.get_state()

        if state[0] == "HIGHPOINT_FOUND" and state[1]:
            if state2[0] == "ABOVE_AVG" and len(trade_bought_positions) > len(trade_sold_positions):
                trade_sold_positions.append(trade_pos)
            else:
                trade_highpoint_positions.append(trade_pos)
        elif state[0] == "LOWPOINT_FOUND" and state[1]:
            if state2[0] == "BELOW_AVG" and len(trade_sold_positions) == len(trade_bought_positions):
                trade_bought_positions.append(trade_pos)
            else:
                trade_lowpoint_positions.append(trade_pos)
        elif state[0] == "UPWARD_SLOPE":
            trade_upward_slope_positions.append(trade_pos)
        elif state[0] == "DOWNWARD_SLOPE":
            trade_downward_slope_positions.append(trade_pos)

        if state2[0] == "ABOVE_AVG":
            trade_above_avg_positions.append(trade_pos)
        elif state2[0] == "BELOW_AVG":
            trade_below_avg_positions.append(trade_pos)

        trade_pos+=1

    elif not trade_done:
        capital = 100000
        length = min(len(trade_highpoint_positions),len(trade_lowpoint_positions))

        for hi_lo_pair in range(length):
            bought_pos = trade_lowpoint_positions[hi_lo_pair]
            sold_pos = trade_highpoint_positions[hi_lo_pair]

            bought_price = get_kline(full_klines[bought_pos])["middle"]
            sold_price = get_kline(full_klines[sold_pos])["middle"]
            capital = capital * (sold_price / bought_price) * 0.999 * 0.999
            print(capital)

        print(capital)
        trade_done = True

pdb.set_trace()

