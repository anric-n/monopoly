import numpy as np

# 123-state model: 40 board positions x 3 doubles-streak levels = 120,
# plus 3 jail-turn states.

JV = 10
GO_TO_JAIL = 30
JAIL1, JAIL2, JAIL3 = 120, 121, 122
N = 123

def s(pos, k):
    return pos*3 + k

def in_jail(state):
    return state >= 120

# dice probabilities, separated by doubles vs not
dice = {}
for a in range(1, 7):
    for b in range(1, 7):
        total = a + b
        if total not in dice:
            dice[total] = [0.0, 0.0]
        if a == b:
            dice[total][0] += 1/36
        else:
            dice[total][1] += 1/36

def nearest_rr(p):
    rrs = [5, 15, 25, 35]
    for r in rrs:
        if r >= p:
            return r
    return 5

def nearest_util(p):
    if p <= 12: return 12
    if p <= 28: return 28
    return 12

# what happens when you land on a square (cards, go-to-jail, etc.)
# returns prob distribution over all 123 states, tagged with streak k
def land(pos, k):
    out = np.zeros(N)
    if pos == GO_TO_JAIL:
        out[JAIL1] = 1.0
        return out
    # chance squares
    if pos == 7 or pos == 22 or pos == 36:
        out[s(pos, k)] += 6/16  # 6 cards do nothing
        # 10 cards that move you, 1/16 each
        targets = [0, 24, 11, 5, nearest_rr(pos), nearest_rr(pos),
                   nearest_util(pos), 'jail', 'back3', 39]
        for t in targets:
            if t == 'jail':
                out[JAIL1] += 1/16
            elif t == 'back3':
                out += (1/16) * land((pos-3) % 40, k)
            else:
                out += (1/16) * land(t, k)
        return out
    # community chest
    if pos == 2 or pos == 17 or pos == 33:
        out[s(pos, k)] += 14/16
        out += (1/16) * land(0, k)  # advance to GO
        out[JAIL1] += 1/16
        return out
    # regular square
    out[s(pos, k)] = 1.0
    return out


# fill in the transition matrix row for state (pos, k)
# turn ends on non-doubles or 3rd consecutive double
def turn_from(pos, k):
    result = np.zeros(N)
    for total, (pd, pn) in dice.items():
        new_pos = (pos + total) % 40
        # non-doubles: turn ends, streak resets
        if pn > 0:
            result += pn * land(new_pos, 0)
        # doubles
        if pd > 0:
            if k == 2:
                # third double in a row -> jail
                result[JAIL1] += pd
            else:
                # roll again. need to compose with another turn from new state
                landed = land(new_pos, k+1)
                for st in range(N):
                    if landed[st] == 0:
                        continue
                    if in_jail(st):
                        result[st] += pd * landed[st]
                    else:
                        sub_pos = st // 3
                        sub_k = st % 3
                        result += pd * landed[st] * turn_from(sub_pos, sub_k)
    return result


T = np.zeros((N, N))

for pos in range(40):
    for k in range(3):
        T[s(pos, k), :] = turn_from(pos, k)

# jail rows. Each turn in jail you roll for doubles; 3rd turn must pay+leave
def jail_row(turn):
    row = np.zeros(N)
    for total, (pd, pn) in dice.items():
        new_pos = (JV + total) % 40
        if pd > 0:
            row += pd * land(new_pos, 0)
        if pn > 0:
            if turn < 3:
                row[JAIL1 + turn] += pn  # advance to next jail turn
            else:
                # turn 3, forced exit
                row += pn * land(new_pos, 0)
    return row

T[JAIL1] = jail_row(1)
T[JAIL2] = jail_row(2)
T[JAIL3] = jail_row(3)

# sanity check rows
for i in range(N):
    if abs(T[i].sum() - 1) > 1e-9:
        print('row', i, 'bad sum:', T[i].sum())

# stationary distribution from left eigenvector at eigenvalue 1
vals, vecs = np.linalg.eig(T.T)
idx = np.argmin(np.abs(vals - 1))
pi = np.real(vecs[:, idx])
pi = pi / pi.sum()

# verify pi @ T = pi
print('||pi T - pi||_inf =', np.max(np.abs(pi @ T - pi)))

# collapse to per-square probabilities for readability
board = np.zeros(40)
for pos in range(40):
    for k in range(3):
        board[pos] += pi[s(pos, k)]
# combine the in-jail states into the jail corner
jail_total = pi[JAIL1] + pi[JAIL2] + pi[JAIL3]
board[10] += jail_total

names = ['Go','Med','CC','Baltic','IncTax','ReadingRR','Oriental','Chance',
         'Vermont','Conn','Jail','StCharles','Electric','States','Virginia',
         'PennRR','StJames','CC','Tennessee','NewYork','FreeParking',
         'Kentucky','Chance','Indiana','Illinois','BORR','Atlantic','Ventnor',
         'Water','Marvin','GoToJail','Pacific','NCarolina','CC','Pennsylvania',
         'ShortLine','Chance','ParkPl','LuxTax','Boardwalk']

print()
print('jail breakdown:')
print('  in-jail (combined):', jail_total)
print('  just visiting:    ', pi[s(10, 0)] + pi[s(10,1)] + pi[s(10,2)])
print('  total at corner:  ', board[10])

print()
print('top 12 spaces:')
ranked = sorted(range(40), key=lambda i: -board[i])
for r, i in enumerate(ranked[:12], 1):
    print(f'{r:2d}. {names[i]:<14} {board[i]*100:6.3f}%')


# ROI table by color group
props = [
    (1,'Brown',60,10),(3,'Brown',60,20),
    (6,'LightBlue',100,30),(8,'LightBlue',100,30),(9,'LightBlue',120,40),
    (11,'Pink',140,50),(13,'Pink',140,50),(14,'Pink',160,60),
    (16,'Orange',180,70),(18,'Orange',180,70),(19,'Orange',200,80),
    (21,'Red',220,90),(23,'Red',220,90),(24,'Red',240,100),
    (26,'Yellow',260,110),(27,'Yellow',260,110),(29,'Yellow',280,120),
    (31,'Green',300,130),(32,'Green',300,130),(34,'Green',320,150),
    (37,'Blue',350,175),(39,'Blue',400,200),
]

groups = {}
for pos, color, price, rent in props:
    if color not in groups:
        groups[color] = [0, 0]  # total cost, total expected rent
    groups[color][0] += price
    groups[color][1] += board[pos] * rent

print()
print('color group ROI:')
ranking = sorted(groups.items(), key=lambda x: -x[1][1]/x[1][0])
for color, (cost, erent) in ranking:
    print(f'  {color:<10} {erent/cost:.5f}')

np.save('pi_123.npy', pi)
np.save('board_pi.npy', board)
