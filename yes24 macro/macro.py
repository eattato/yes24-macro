import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import datetime

print("크롬 프로필 경로를 입력하세요. 크롬에 chrome://version을 주소창에 입력해 확인 가능합니다.")
print("예시: C:\\Users\\umjunsik\\AppData\\Local\\Google\\Chrome\\User Data\\")
chromeDirec = input()

print("예약할 사이트 주소를 입력하세요.")
print("예시: http://ticket.yes24.com/Special/42452")
targetUrl = input()

print("좌석 등급 우선순위를 정확히 입력하세요.")
print("예시: R석 E석 A석")
targetSeats = input().split(" ")

print("예약 날짜를 입력하세요.")
print("예시(10일 또는 11일): 10 11")
bookingDate = input().split(" ")

print("예약 시간을 입력하세요.")
print("예시: 18 05")
bookingTime = input().split(" ")
bookingTime = int(bookingTime[0]) * 3600 + int(bookingTime[1]) * 60

defaultTimeout = 5 # 시간 초과
ticketClass = "rn-bb03" # 티켓 버튼 클래스명

options = webdriver.ChromeOptions() # 드라이버 설정
options.add_argument("user-data-dir=" + chromeDirec) # 쓰던 크롬으로 열게 설정
driver = webdriver.Chrome(options=options) # 크롬드라이버 사용
driver.get(targetUrl) # 대상 URL로 이동

def waitUntilLoad(target, timeout = 5, refresh = False, by = By.CLASS_NAME): # 대상 로딩 대기 함수
    elem = False
    try:
        print(target + "을 찾는 중..")
        elem = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, target)))
        print(target + "을 찾음")
    except TimeoutException:
        elem = False
        if refresh == True:
            print("시간 초과, 새로고침 합니다..")
            driver.refresh() # 타임아웃 시 새로고침
            waitUntilLoad(target, timeout, refresh)
        else:
            print("시간 초과")
    finally:
        return elem

while True:
    currentTime = str(datetime.datetime.now().time())
    currentTime = currentTime.split(":")
    currentTime = int(currentTime[0]) * 3600 + int(currentTime[1]) * 60 + int(currentTime[2].split(".")[0])

    if currentTime - 3 >= bookingTime:
        driver.refresh()
        driver.implicitly_wait(1)
        ticketButton = driver.find_element(By.CLASS_NAME, ticketClass)
        if ticketButton:
            break

ticket = waitUntilLoad(ticketClass) # 예약 버튼 
if ticket:
    print("예약 버튼 발견")
    ticket.click()
    print("예약 창 대기 중..")
    while len(driver.window_handles) <= 1:
        driver.implicitly_wait(1)
    print("예약 창으로 이동합니다..")
    driver.switch_to.window(driver.window_handles[1]) # 새 창으로 이동
    print("예약 창으로 이동했습니다. " + driver.title)
    
    while len(driver.find_elements(By.TAG_NAME, "td")) < 35: # 날짜 모두 로딩 될 때 까지
        driver.implicitly_wait(0.1)
    print("예약 날짜 로딩됨")
    selects = driver.find_elements(By.CLASS_NAME, "select") # 예약 날짜 버튼

    # print(selects)
    foundSeat = False
    seatSpace = waitUntilLoad(target="ulSeatSpace", by=By.ID)
    seatSelectBtn = waitUntilLoad(target="btnSeatSelect", by=By.ID)
    seatTiming = waitUntilLoad(target="ulTime", by=By.ID)
    if len(selects) > 0:
        print("예약 가능한 날짜가 있습니다.")
        for select in selects: # 모든 가능한 날짜 조회
            targetClass = False

            link = select.find_element(By.TAG_NAME, "a")
            if link:
                datePossible = False
                for dateCheck in bookingDate:
                    if link.text == dateCheck:
                        datePossible = True
                        break

                if datePossible == True:
                    print(link.text + "일 예약 가능")
                    select.click()
                    while len(seatTiming.find_elements(By.TAG_NAME, "li")) < 1: # 시간대 나타날 때까지 대기
                        driver.implicitly_wait(0.1)

                    for timing in seatTiming.find_elements(By.TAG_NAME, "li"):
                        print(timing.text + " 조회중..")
                        timing.click() # 시간대 선택
                        time.sleep(0.5)
                        while len(seatSpace.find_elements(By.TAG_NAME, "li")) < 1: # 좌석 등급 나타날 때까지 대기
                            driver.implicitly_wait(0.1)
                        
                        # 예약 대상 좌석이 존재하는지 미리 확인
                        print("좌석 등급 대상 {}개".format(len(targetSeats)))
                        for seatClass in targetSeats: # 대상 좌석을 모두 조회
                            for seat in seatSpace.find_elements(By.TAG_NAME, "li"):
                                # WebDriverWait(driver, defaultTimeout).until(EC.presence_of_element_located((By.TAG_NAME, "strong")))
                                currentClass = seat.find_element(By.TAG_NAME, "strong").text
                                seatText = seat.find_element(By.TAG_NAME, "span") # 현재 좌석수
                                current = seatText.text.split("석")[0]
                                # print("대상:" + seatClass + " 조회-" + currentClass + " " + current + "석")
                                if seatClass == currentClass: # 좌석이 남아있고 대상인 좌석인지 확인
                                # if current != "0" and seatClass == currentClass: # 좌석이 남아있고 대상인 좌석인지 확인
                                    print(seatClass + " 현재 {}석 남았습니다.".format(current))
                                    targetClass = seatClass # 예매할 좌석을 미리 선택
                                    break

                        # 예약 대상인 좌석이 존재한다면 좌석 선택 시작
                        if targetClass != False:
                            print(targetClass + " 등급으로 구역을 선택합니다..")
                            seatSelectBtn.click() # 좌석선택 버튼 클릭
                            iframe = waitUntilLoad(target="ifrmSeatFrame", by=By.NAME)
                            time.sleep(1)
                            driver.switch_to.frame(iframe) # 예매 iframe으로 이동
                            seatPosList = waitUntilLoad(target="ulLegend", by=By.ID) # 좌석 등급 별 좌석 목록
                            seatSelected = waitUntilLoad(target="liSelSeat", by=By.ID) # 선택된 좌석 목록
                            booking = waitUntilLoad(target="booking") # 선택 완료 버튼
                            while len(seatPosList.find_elements(By.TAG_NAME, "div")) < 1: # 좌석 등급 대기
                                driver.implicitly_wait(0.1)
                            for seat in seatPosList.find_elements(By.TAG_NAME, "div"): # 오른쪽 좌석 등급 리스트를 열어 조회
                                print(seat.find_element(By.TAG_NAME, "p").text.split(" ")[0] + " 조회 중..")
                                if seat.find_element(By.TAG_NAME, "p").text.split(" ")[0] == targetClass: # 조회 중인 좌석 등급이 맞다면
                                    seat.click() # 해당 좌석 등급을 선택
                                    seatLayer = waitUntilLoad(target="seat_layer") # 좌석 구역 ul 로드
                                    while len(seatLayer.find_elements(By.TAG_NAME, "li")) < 1: # 좌석 구역 리스트 대기
                                        driver.implicitly_wait(0.1)
                                    print("좌석 구역 리스트 로드됨")
                                    seatAreaList = seatLayer.find_elements(By.TAG_NAME, "li") # 해당 등급의 좌석 구역 리스트
                                    for seatArea in seatAreaList: # 좌석 구역 모두 조회
                                        areaCurrent = seatArea.text.split("(")[1].split("석")[0] # 해당 구역의 좌석 수
                                        if areaCurrent != "0": # 해당 구역에 좌석이 있다면
                                            print(seatArea.text + " 선택됨")
                                            seatArea.click() # 해당 구역 버튼을 클릭

                                            # 구역 좌석 리스트 창으로 넘어간 뒤 예약까지 하기
                                            seatList = waitUntilLoad(target="divSeatArray", by=By.ID) # 좌석 위치 리스트
                                            while len(seatList.find_elements(By.TAG_NAME, "div")) < 1: # 좌석 위치 리스트 대기
                                                driver.implicitly_wait(0.1)
                                            for seatPos in seatList.find_elements(By.TAG_NAME, "div"):
                                                seatTitle = seatPos.get_attribute("title")
                                                if len(seatTitle) != 0:
                                                    seatPos.click() # 해당 좌석 위치 클릭
                                                    driver.implicitly_wait(0.1)
                                                    selected = seatSelected.find_elements(By.TAG_NAME, "p")
                                                    if len(selected) > 0:
                                                        print(seatTitle + " 선택됨")
                                                        booking.click() # 좌석 선택 버튼 클릭
                                                        foundSeat = True
                                                        break

                                            if foundSeat == True:
                                                break
                                    print("좌석 조회 완료")
                                    break # 좌석을 조회했으니 탈출
                        else:
                            print("대상 등급인 좌석이 없습니다. 다음 날짜로 이동합니다.")

                        if foundSeat == True:
                            break
                    if foundSeat == True:
                        break
                
        if foundSeat == True:
            print("좌석을 선택했습니다. 결제하세요.")
            while True:
                time.sleep(600)
    else:
        print("예약 가능한 날짜가 없습니다..")
else:
    print("예약 버튼을 찾지 못했습니다..")