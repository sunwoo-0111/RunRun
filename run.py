import time
import pygame as pg
from PIL import Image, ImageDraw, ImageFont
import random

from pygame.examples.aliens import Player

# 파이게임 초기화 240x240
pg.init()
screen = pg.display.set_mode((240, 240))
clock = pg.time.Clock()

#최고점수 로딩
try:
    with open ("score.txt", 'r', encoding="utf-8") as f:
        high_score = int(f.read())
except:
    high_score = 0

# 시작화면
def start_game():
    start_image = Image.open("/Users/limsunwoo/runrun/images/Start.png").convert("RGB")
    draw = ImageDraw.Draw(start_image)
    
    print(start_image.size)
    print(start_image.mode)
    font_path = "/Users/limsunwoo/runrun/font/continuous.ttf"
    font_large = ImageFont.truetype(font_path, size=20)
    font_small = ImageFont.truetype(font_path, size=12)

    draw.text((60,50),"Run!! Run!!",fill=(255,0,0),font=font_large)
    draw.text((60,200), "Press A to start", fill=(0,0,0), font=font_small)

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_a:  # A 키를 누르면 시작
                    print("a key pressed")
                    running = False

        # 이미지를 PyGame 화면에 출력
        screen.blit(pg.image.fromstring(start_image.tobytes(), start_image.size, "RGB"), (0, 0))
        pg.display.flip()
        clock.tick(15)


restart = True


def Game():
    global restart, high_score
    restart = False
    
    backgroundImage = Image.open("/Users/limsunwoo/runrun/images/background.png").convert("RGB")
    

    block = []
    for i in range(20):
        block.append([i * 12, 240 - 12])

    isblock = True
    holeCount = 0
    score = 0
    lives = 3
    invincible_until = 0


    def newMap(block, isblock, holeCount):
        if isblock:
            block.append([240, 240 - 12])  # 바닥
        else:
            holeCount += 1

        if random.randint(0, 4) == 0 or holeCount > 3:
            block.append([240,240-24])
            block.append([240,240-12])
            isblock = not isblock
            holeCount = 0

    # 도둑 구현
    playerPos = [12 * 10, 10 * 12]
    playerSize = [12, 24]

    playerImage = Image.new("RGB", (12, 24), (255, 0, 0))
    drawPlayerImage = ImageDraw.Draw(playerImage)
    drawPlayerImage.rectangle((6, 3, 12, 7), (0, 255, 0))

    playerSlideImage = Image.new("RGB", (24, 12), (255, 0, 0))
    drawPlayerImage = ImageDraw.Draw(playerSlideImage)
    drawPlayerImage.rectangle((3, 0, 7, 6), (0, 255, 0))

    # 추격자 구현
    chaserPos = [0 ,10*12]
    chaserSize = [24, 24]

    chaserImage = Image.new("RGB", (24,24), (0,0,255))
    drawchaserImage = ImageDraw.Draw(chaserImage)
    drawPlayerImage.rectangle((6, 3, 12, 7), (0, 255, 0))

    playerVerticalSpeed = 0
    jumpable = False
    playerSlide = False


    # 충돌 함수
    def collision(playerPos,playerSize, other):  # 0: no collision, 1: top, 2: bottom, 3: left, 4: right

        player_left, player_right = playerPos[0], playerPos[0] + playerSize[0]
        player_top, player_bottom = playerPos[1], playerPos[1] + playerSize[1]

        other_left, other_right = other[0], other[0] + 12
        other_top, other_bottom = other[1], other[1] + 12

        if player_right > other_left and player_left < other_right:
            if player_bottom > other_top and player_top < other_bottom:
                distances = {
                    1: abs(player_bottom - other_top),  # top
                    2: abs(player_top - other_bottom),  # bottom
                    3: abs(player_right - other_left),  # left
                    4: abs(player_left - other_right),  # right
                }
                return min(distances, key=distances.get)
        return 0


    
    # 게임 루프
    running = True
    while running:
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        keys = pg.key.get_pressed()
        if keys[pg.K_UP]:
            if jumpable:
                playerVerticalSpeed -= 8 
                jumpable = False

        if keys[pg.K_DOWN]:
            playerSlide = True
        else:
            if playerSlide:
                playerPos[1]-=12
            playerSlide = False

        if score % 4 == 0:
            newMap(block, isblock, holeCount)
        score += 1

        playerPos[1] += playerVerticalSpeed
        playerVerticalSpeed += 1
        playerVerticalSpeed = min(playerVerticalSpeed, 5)

        usePlayerImage = playerImage.copy()
        if playerSlide:
            playerSize = [24, 12]
            usePlayerImage=playerSlideImage
        else:
            playerSize = [12,24]

        jumpable = False
        # 충돌 체크
        for b in block:
            col = collision(playerPos,playerSize, b)
            if col == 1:
                playerPos[1] = b[1] - playerSize[1]
                playerVerticalSpeed = 0
                jumpable = True
            elif col == 2:
                playerPos[1] = b[1] + playerSize[1]
                playerVerticalSpeed = 0
            elif col == 3: #벽에 부딫히면 목숨 소모,그리고 1초동안 무적 상태
                if time.time() > invincible_until:
                    lives -= 1
                    invincible_until = time.time() + 1 # 1초 무적
                    if lives == 0:
                        running = False
                playerPos[0] = b[0] - playerSize[0]

        if time.time() < invincible_until:
            usePlayerImage = usePlayerImage.point(lambda p:p//2)

        # 적군
        # enemyCol = collision(enemy)

        # 맵 이미지 좌측을 없애가며 이동
        bg = backgroundImage.copy()
        draw = ImageDraw.Draw(bg)
        for b in block:
            draw.rounded_rectangle((
                b[0], b[1], b[0] + 12, b[1] + 12
            ), 2, (0, 0, 0))
            b[0] -= 3

        # running 중 현재점수, 남은 목숨 , 최고점수 띄우기
        font = ImageFont.load_default()
        draw.text((5,5), f"Score: {score}", fill=(0,0,0), font=font)
        draw.text((200,5), f"Lives: {lives}", fill=(255,0,0), font=font)
        draw.text((100,5),f"high: {high_score}", fill=(0,0,0),font=font)

        # 플레이어 이미지 그리기
        bg.paste(usePlayerImage, (int(playerPos[0]), int(playerPos[1])))

        # break
        if playerPos[1] > 240:
            running = False

        screen.blit(pg.image.fromstring(bg.tobytes(), bg.size, "RGB"), (0, 0))
        pg.display.flip()
        clock.tick(15)

    bg = backgroundImage.copy()
    draw = ImageDraw.Draw(bg)
    for b in block:
        draw.rounded_rectangle((
            b[0], b[1], b[0] + 12, b[1] + 12
        ), 2, (0, 0, 0))



    # 플레이어 이미지 그리기
    bg.paste(playerImage, (int(playerPos[0]), int(playerPos[1])))

    
    # 게임 오버 화면
    isScoreDraw = False
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_a:
                    restart = True
                    return

        bg_ = bg.copy()
        draw = ImageDraw.Draw(bg_)

        # 결과 점수 반환 및 재시작 여부
        if isScoreDraw:
            font_path = "/Users/limsunwoo/runrun/font/continuous.ttf"
            font = ImageFont.truetype(font_path, size = 20)
            draw.text((110,90), str(score), fill=(0, 0, 0), font=font)
            draw.text((45,140), f"Press A to restart", fill=(0,0,0), font=font)
            
            if score > high_score:
                high_score = score
            
            with open ("score.txt",'w',encoding='utf-8') as f:
                f.write(str(high_score))
            
        isScoreDraw = not isScoreDraw

        screen.blit(pg.image.fromstring(bg_.tobytes(), bg_.size, "RGB"), (0, 0))
        pg.display.flip()

        time.sleep(0.5)

while(True):
    start_game()
    while(restart):
        Game()