import time
import random
from colorsys import hsv_to_rgb
import board
from gpiozero import Button
from digitalio import DigitalInOut
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789

# 디스플레이 생성
cs_pin = DigitalInOut(board.CE0)
dc_pin = DigitalInOut(board.D25)
reset_pin = DigitalInOut(board.D24)
BAUDRATE = 24000000  # SPI 통신 속도 조절

spi = board.SPI()
disp = st7789.ST7789(
    spi,
    height=240,
    y_offset=80,
    rotation=180,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
)

# 입력 핀:
button_A = Button(5)
button_B = Button(6)
button_L = Button(27)
button_R = Button(23)
button_U = Button(17)
button_D = Button(22)
button_C = Button(4)

# 백라이트 켜기
backlight = DigitalInOut(board.D26)
backlight.switch_to_output()
backlight.value = True

#최고점수 로딩
try:
    with open ("score.txt", 'r', encoding="utf-8") as f:
        high_score = int(f.read())
except:
    high_score = 0

# 시작화면
def start_game():
    start_image = Image.open("images/Start.png").convert("RGB")
    draw = ImageDraw.Draw(start_image)
    
    print(start_image.size)
    print(start_image.mode)
    font_path = "font/continuous.ttf"
    font_large = ImageFont.truetype(font_path, size=20)
    font_small = ImageFont.truetype(font_path, size=12)

    draw.text((60,130),"Run!! Run!!",fill=(255,255,0),font=font_large,)
    draw.text((80,200), "Press A to start", fill=(255,0,0), font=font_small)

    running = True
    while running:
        if button_A.is_pressed:
            running = False

        # 이미지를 화면에 출력
        disp.image(start_image)


restart = True


def Game():
    global restart, high_score
    restart = False
    
    backgroundImage = Image.open("images/background.png").convert("RGB")

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
            print("holecounted")
            holeCount += 1

        if random.randint(0, 4) == 0 or holeCount > 3:
        # 기둥의 높이를 랜덤으로 설정 (24, 36 중 하나)
            obstacleHeight = random.choice([24, 36])
            block.append([240, 240 - obstacleHeight])
            isblock = not isblock
            holeCount = 0
        else:
        # 구멍의 크기를 랜덤으로 설정 (1칸, 2칸, 3칸)
            hole_size = random.randint(1, 3)  # 1칸에서 3칸 사이의 구멍 크기
            if holeCount < 3:  # 구멍이 3칸 이하일 때만 구멍 생성
                block.append([240, 240 - (hole_size * 12)])  # 구멍의 높이를 12씩 곱하여 설정
        return isblock, holeCount

    # 도둑 구현
    playerPos = [12 * 10, 10 * 12]
    playerSize = [12, 24]

    playerImage = Image.open("images/Thief1.png").convert("RGBA")
    playerImage_ = Image.open("images/Thief1_.png").convert("RGBA")

    playerSlideImage = Image.open("images/sliding.png")
    playerSlideImage_ = Image.open("images/sliding_.png")

    # 추격자 구현
    chaserPos = [-24 ,playerPos[1]]
    chaserSize = [24, 24]
    chaserSpeed = 2
    chaserActive = False

    playerVerticalSpeed = 0
    jumpable = False
    playerSlide = False

    # 추격자 그리기
    chaserImage = Image.open("images/chaser.png")

    # 목숨 아이템 구현
    heartPos = None
    heartTimer = 0

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
    paused = False
    font_path = "font/continuous.ttf"
    font_12 = ImageFont.truetype(font_path, size = 12)
    font_20 = ImageFont.truetype(font_path, size = 20)
    
    def paused_game():
        nonlocal paused
        paused = not paused
    while running:
        
        button_C.when_pressed = paused_game
   
        if button_U.is_pressed:
            if jumpable:
                playerVerticalSpeed -= 8 
                jumpable = False

        if button_D.is_pressed:
            playerSlide = True
        else:
            if playerSlide:
                playerPos[1]-=12
            playerSlide = False

        if score % 4 == 0:
            newMap(block, isblock, holeCount)
        score += 1


        playerPos[1] += playerVerticalSpeed
        playerVerticalSpeed += 1.2
        playerVerticalSpeed = min(playerVerticalSpeed, 5)

        if time.time() < invincible_until:
            invincible = True # 무적 상태 활성화 플래그
        else:
            invincible = False # 다시 끄기

        if invincible:
            usePlayerImage = playerImage_.copy()
            if playerSlide:
                playerSize = [24, 12]
                usePlayerImage = playerSlideImage_.copy()
            else:
                playerSize = [12, 24]

        else:
            usePlayerImage = playerImage.copy()
            if playerSlide:
                playerSize = [24, 12]
                usePlayerImage = playerSlideImage.copy()
            else:
                playerSize = [12, 24]

        jumpable = False
        # 충돌했을 때 벽에 밀려 위치가 애매해지는 현상 해결
        # 충돌 체크
        for b in block:
            if b[0] > 140:
                continue
            if b[0] < -20:
                block.remove(b)
                continue
            col = collision(playerPos,playerSize, b)
            if col == 1:
                playerPos[1] = b[1] - playerSize[1]
                playerVerticalSpeed = 0
                jumpable = True
            elif col == 2:
                playerPos[1] = b[1] + playerSize[1]
                playerVerticalSpeed = 0
            elif col == 3: #벽에 부딫히면 목숨 소모,그리고 1초동안 무적 상태 그리고 원래위치 돌아오기
                if time.time() > invincible_until:
                    lives -= 1
                    invincible_until = time.time() + 1 # 1초 무적
                    if lives == 0:
                        running = False
                playerPos[0] = b[0] - playerSize[0]


        #recovering
        if playerPos[0] < 120:
            playerPos[0] += 1.5
            if playerPos[0] == 120:
                playerPos[0] = 120

        # 추격자 활성화 조건
        if lives == 2 and not chaserActive:
            chaserActive = True
            chaserPos = [-24, 240-36]

        # 추격자 이동 로직 (묵숨이 달때 쫒아오는것 + 목숨을 먹었을 때 멀어지는 것 까지 구현)
        if chaserActive:
            if invincible:
                if(playerPos[0]<120):
                    chaserPos[0] += chaserSpeed
                else:
                    if lives >= 3:
                        chaserPos[0] -= 1
                        if chaserPos[0] == 0:
                            chaserPos[0] = 0
                    elif lives == 2:
                        if chaserPos[0] < playerPos[0] - 60: 
                            chaserPos[0] += chaserSpeed
                        elif chaserPos[0] > playerPos[0] - 60:
                            chaserPos[0] -= 1
                        else:
                            chaserPos[0] = playerPos[0]- 60
                    elif lives == 1:
                        if chaserPos[0] < playerPos[0] - 40:
                            chaserPos[0] += chaserSpeed
                        else:
                            chaserPos[0] = playerPos[0] - 40
            else:
                if lives >= 3:
                    chaserPos[0] -= 1
                    if chaserPos[0] == 0:
                        chaserPos[0] = 0
                elif lives == 2:
                    if chaserPos[0] < playerPos[0] - 60: 
                        chaserPos[0] += chaserSpeed
                    elif chaserPos[0] > playerPos[0] - 60:
                        chaserPos[0] -= 1
                    else:
                        chaserPos[0] = playerPos[0]- 60
                elif lives == 1:
                    if chaserPos[0] < playerPos[0] - 40:
                        chaserPos[0] += chaserSpeed
                    else:
                        chaserPos[0] = playerPos[0] - 40
            

        #추격자에게 잡히면 게임 끝
        if (chaserPos[0] + chaserSize[0] >= playerPos[0] and 
        chaserPos[0] <= playerPos[0] + playerSize[0] and 
        chaserPos[1] + chaserSize[1] >= playerPos[1] and 
        chaserPos[1] <= playerPos[1] + playerSize[1]):
            running = False  # 게임 오버

        
        # 맵 이미지 좌측을 없애가며 이동
        bg = backgroundImage.copy()
        draw = ImageDraw.Draw(bg)
        for b in block:
            draw.rounded_rectangle((
                b[0], b[1], b[0] + 12, b[1] + 12
            ), 2, (0, 0, 0))
            if(score < 200):
                b[0] -= 3
            elif(score < 400):
                b[0] -= 3.5
            elif(score < 600):
                b[0] -= 4
            else:
                b[0] -= 6

        # running 중 현재점수, 남은 목숨 , 최고점수 띄우기
        
        if(score <= high_score):
            draw.text((5,5), f"Score: {score}", fill=(0,0,0), font=font_12)
        else:
            draw.text((5,5), f"Score: {score}", fill=(255,0,0), font=font_12)
        draw.text((200,5), f"Lives: {lives}", fill=(255,0,0), font=font_12)
        draw.text((100,5),f"high: {high_score}", fill=(0,0,0),font=font_12)

        # 플레이어 이미지 그리기
        bg.paste(usePlayerImage, (int(playerPos[0]), int(playerPos[1])))
        bg.paste(chaserImage, (int(chaserPos[0]),int(chaserPos[1])))
        # 하트 아이템 구현

        heartImage = Image.open("images/heart.png")
        if heartPos is None and lives<3 and random.randint(0,100) < 1:
            heartPos = [240,240-36]
        
        if heartPos:
            bg.paste(heartImage, (heartPos[0],heartPos[1]))
            heartPos[0] -= 3
            if (heartPos[0] <= playerPos[0] + 12 and heartPos[0] + heartImage.width >= playerPos[0] and
                heartPos[1] >= playerPos[1] and heartPos[1] <= playerPos[1] + 24):
                    heartPos = None
                    lives += 1
            elif heartPos[0] < -2:
                heartPos = None
            
        # break
        if playerPos[1] > 240:
            running = False

        disp.image(bg)
        time.sleep(0.01)

    bg = backgroundImage.copy()
    draw = ImageDraw.Draw(bg)
    for b in block:
        draw.rounded_rectangle((
            b[0], b[1], b[0] + 12, b[1] + 12
        ), 2, (0, 0, 0))

    # 플레이어와 추격자 이미지 그리기
    bg.paste(playerImage, (int(playerPos[0]), int(playerPos[1])))
    bg.paste(chaserImage, (int(chaserPos[0]), int(chaserPos[1])))
    # 게임 오버 화면
    isScoreDraw = False
    while True:
        if button_A.is_pressed:
            restart = True
            break

        bg_ = bg.copy()
        draw = ImageDraw.Draw(bg_)

        # 결과 점수 반환 및 재시작 여부
        
        if isScoreDraw:
            draw.text((110,90), str(score), fill=(0, 0, 0), font=font_20)
            draw.text((45,140), f"Press A to restart", fill=(0,0,0), font=font_20)
            
            if score > high_score:
                high_score = score

            with open ("score.txt",'w',encoding='utf-8') as f:
                f.write(str(high_score))
            
        isScoreDraw = not isScoreDraw

        disp.image(bg_)
        time.sleep(0.1)

while(True):
    start_game()
    while(restart):
        Game()
        
