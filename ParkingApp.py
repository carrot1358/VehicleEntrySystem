import requests
import PySimpleGUI as sg
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import webbrowser
import ParkingLot

BAR_WIDTH = 10  # width of each bar
BAR_SPACING = 14  # space between each bar
EDGE_OFFSET = 3  # offset from the left edge for first bar
GRAPH_SIZE = (500, 500)  # size in pixels

def convert_to_bytes(file_or_bytes, resize=None):
    if isinstance(file_or_bytes, str):
        img = Image.open(file_or_bytes)
    else:
        try:
            img = Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))
        except Exception as e:
            dataBytesIO = io.BytesIO(file_or_bytes)
            img = Image.open(dataBytesIO)

    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height / cur_height, new_width / cur_width)
        img = img.resize((int(cur_width * scale), int(cur_height * scale)), Image.LANCZOS)
    with io.BytesIO() as bio:
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()

class ParkingApp:
    def __init__(self):
        self.current_page = 0
        self.items_per_page = 10
        self.window1 = self.make_win1()
        self.window2 = None
        self.parking_history = []

    def make_win1(self):
        sg.theme("LightBlue2")
        self.parking_lot = ParkingLot.ParkingLot()

        menu_def = [['&File', ['About','Document', 'Exit']],
                    ['&Debug', ['Random Car', 'Random History Car','Remove Debug Car']],]
        left_col = [[sg.MenubarCustom(menu_def, pad=(0,0), k='-CUST MENUBAR-')],
                    [sg.Text("ระบบจอดรถ", font=("Helvetica", 20))],
                    [sg.Text("เลือกไฟล์รูปภาพ:"), sg.InputText(key="filePath", size=(42, 5)), sg.FileBrowse(),
                     sg.Button("สแกนทะเบียน")],
                    [sg.Text("เลขทะเบียน:"), sg.InputText(key="license_plate", size=(37, 5)), sg.Button("รถเข้าจอด"),
                     sg.Button("แก้ไข"),sg.Button("รายละเอียดรถ")],
                    [sg.Text("เวลา :"), sg.InputText(key="hours", size=(10, 5), default_text="0"), sg.Text("ชม"),
                     sg.InputText(key="minutes", size=(10, 5), default_text="0"), sg.Text("นาที"),
                     sg.InputText(key="seconds", size=(10, 5), default_text="0"), sg.Text("วินาที")],
                    [sg.Table(values=[], headings=["ทะเบียนรถ", "เวลาที่เหลือ", "เวลาเกิน"], key="table",
                              justification="center", auto_size_columns=False, col_widths=[20, 20, 20],
                              enable_events=True)],
                    [sg.Button("Graph"), sg.Button("ประวัติรถเข้า-ออก")]]
        images_col = [[sg.Column([[sg.Text('รายละเอียดรถ:')]], element_justification='c')],
                      [sg.Column([[sg.Text(size=(40, 1), key='-license_plate-')]], element_justification='c')],
                      [sg.Image(key='-IMAGE-')],
                      [sg.Button("รถออก", visible=False, key="รถออก")]]
        self.layout = [
            [sg.Column(left_col, element_justification='c'),
             sg.VSeperator(),
             sg.Column(images_col, element_justification='c', vertical_alignment='top')]
        ]
        self.window = sg.Window("ระบบจอดรถ", self.layout, finalize=True)

    def make_win2(self):
        layout = [[sg.Text('Chart of Cars Out', size=(30, 1), justification='center', font='Helvetica 20')],
                  [sg.Graph(GRAPH_SIZE, (0, -380), (GRAPH_SIZE[0] // 2, GRAPH_SIZE[1] // 2),
                            k='-GRAPH-')],
                  [sg.Button('Sort by Remaining Time'), sg.Button('Sort by Overtime')],

                  [sg.Exit(), sg.Button('Next'), sg.Button('Previous')]]
        self.window2 =  sg.Window('Bar Graph', layout, finalize=True)
        return self.window2

    def run(self):
        page = 1
        while True:
            window, event, values = sg.read_all_windows(timeout=1000)
            # print(f"Event: {window} : {event}")
            if window == self.window and event == sg.WIN_CLOSED:
                print("window1 closed")
                break
            elif window == self.window1 and event == "Graph":
                if self.window2 is None:
                    self.parking_lot.draw_bar_chart(self.parking_lot.carsOut)
                    self.window2 = self.make_win2()
            elif window == self.window2 and event == sg.WIN_CLOSED:
                print("window2 closed")
                self.window2.close()
                self.window2 = None
            elif window == self.window2 and event == "Exit":
                print("window2 closed")
                self.window2.close()
                self.window2 = None
            elif event == 'Sort by Remaining Time':
                self.parking_lot.carsOut = dict(sorted(self.parking_lot.carsOut.items(),
                                                       key=lambda item: item[1]['remaining_time'],
                                                       reverse=True))
                self.draw_bar_chart(self.parking_lot.carsOut, isShowRemainingTime=True, isShowOvertime=False)
            elif event == 'Sort by Overtime':
                self.parking_lot.carsOut = dict(sorted(self.parking_lot.carsOut.items(),
                                                       key=lambda item: item[1]['overtime'],
                                                       reverse=True))
                self.draw_bar_chart(self.parking_lot.carsOut, isShowRemainingTime=False, isShowOvertime=True)
            elif event == 'Exit':
                break
            elif event == 'About':
                sg.popup('Properties', 'Version 1.0', 'For Python 3.12', 'Based on PySimpleGUI', 'Made by Nattapad & Teerapat','Github : https://github.com/carrot1358/VehicleEntrySystem',button_justification='center', keep_on_top=True)
            elif event == 'Document':
                url = 'https://panoramic-file-85b.notion.site/VehicleEntrySystem-Manual-5c05c39cfb6d406da09a17f1a4c27a61'
                webbrowser.open(url)
            elif event == 'Random Car':
                while True:
                    num_cars = sg.popup_get_text('ใส่จำนวนรถที่ต้องการเพิ่ม', default_text='5', )
                    if num_cars == None:
                        break
                    elif (num_cars.isnumeric() == False):
                        sg.popup("กรุณาใส่ตัวเลข")
                    elif (int(num_cars) > 1000):
                        sg.popup("กรุณาใส่ตัวเลขไม่เกิน 1000")
                    else:
                        break
                if num_cars != None:
                    self.parking_lot.generate_random_cars(int(num_cars))
                    print(self.parking_lot.carsOut)
            elif event == 'Random History Car':
                while True:
                    num_cars = sg.popup_get_text('ใส่จำนวนรถที่ต้องการเพิ่ม', default_text='5', )
                    if num_cars == None:
                        break
                    elif (num_cars.isnumeric() == False):
                        sg.popup("กรุณาใส่ตัวเลข")
                    elif(int(num_cars) > 1000):
                        sg.popup("กรุณาใส่ตัวเลขไม่เกิน 1000")
                    else:
                        break
                if num_cars != None:
                    self.parking_lot.generate_random_cars_out(int(num_cars))
                    print(self.parking_lot.carsOut)
            elif event == 'Remove Debug Car':
                self.parking_lot.remove_Debugcar()
            elif event == "สแกนทะเบียน":
                if (values["license_plate"] == ""):
                    if (values["filePath"] == ""):
                        sg.popup("กรุณาเลือกไฟล์รูปภาพ")
                    elif (values["filePath"][-3:] != "jpg" and values["filePath"][-3:] != "png"):
                        sg.popup("ไฟล์รูปภาพไม่ถูกต้อง")
                    elif (values["filePath"][-3:] == "jpg" or values["filePath"][-3:] == "png"):
                        self.scan_license_plate(values)
                else:
                    sg.popup("กรุณาลบเลขทะเบียนก่อน")
            elif event == "แก้ไข":
                if(values["license_plate"] == ""):
                    sg.popup("กรุณากรอกเลขทะเบียน")
                elif(values["license_plate"] not in self.parking_lot.cars):
                    sg.popup("ไม่พบเลขทะเบียนในระบบ")
                elif (values["hours"].isnumeric() == False or values["minutes"].isnumeric() == False or values["seconds"].isnumeric() == False):
                    sg.popup("กรุณากรอกเวลาให้ถูกต้อง")
                    window["hours"].update('0')
                    window["minutes"].update('0')
                    window["seconds"].update('0')
                elif (int(values["hours"]) > 24 or int(values["minutes"]) > 60 or int(values["seconds"]) > 60):
                    sg.popup("กรุณากรอกเวลาให้ถูกต้อง")
                    window["hours"].update('0')
                    window["minutes"].update('0')
                    window["seconds"].update('0')
                elif (values["hours"] == "0" and values["minutes"] == "0" and values["seconds"] == "0"):
                    sg.popup("กรุณากรอกเวลา")
                else:
                    self.parking_lot.editExpiration_time(values["license_plate"], int(values["hours"]), int(values["minutes"]), int(values["seconds"]))
                    sg.popup("แก้ไขเวลาสำเร็จ")
                    window["license_plate"].update("")
            elif event == "รถเข้าจอด":
                # if lecense plate is special character
                if(values["license_plate"].isalnum() == False):
                    sg.popup("เลขทะเบียนไม่สามารถใส่อักษรพิเศษได้")
                elif(len(values["license_plate"]) > 8):
                    sg.popup("เลขทะเบียนไมjควรเกิน 8 ตัวอักษร")
                elif (values["license_plate"] in self.parking_lot.cars):
                    sg.popup("รถทะเบียนนี้อยู่ในระบบแล้ว")
                elif(values["hours"].isnumeric() == False or values["minutes"].isnumeric() == False or values["seconds"].isnumeric() == False):
                    sg.popup("กรุณากรอกเวลาให้ถูกต้อง")
                    window["hours"].update('0')
                    window["minutes"].update('0')
                    window["seconds"].update('0')
                elif (values["license_plate"] == ""):
                    sg.popup("กรุณากรอกเลขทะเบียน")
                elif(int(values["hours"]) > 24 or int(values["minutes"]) > 60 or int(values["seconds"]) > 60):
                    sg.popup("กรุณากรอกเวลาไม่เกิน 24 ชม. 60 นาที 60 วินาที")
                    window["hours"].update('0')
                    window["minutes"].update('0')
                    window["seconds"].update('0')
                elif (values["hours"] == "0" and values["minutes"] == "0" and values["seconds"] == "0"):
                    sg.popup("กรุณากรอกเวลา")
                else:
                    self.add_car(values)
            elif event == "รถออก":
                if (values["license_plate"] == ""):
                    sg.popup("กรุณากรอกเลขทะเบียน")
                else:
                    sg.popup(f"รถออกแล้ว {values["license_plate"]}",
                             f"เวลาที่เหลือ {self.parking_lot.format_remaining_time(self.parking_lot.cars[values["license_plate"]]['remaining_time'])}",
                             f"เวลาเกิน {self.parking_lot.format_remaining_time(self.parking_lot.cars[values["license_plate"]]['overtime'])}"
                             )
                    self.window["รถออก"].update(visible=False)
                    self.window['-license_plate-'].update("")
                    self.window['-IMAGE-'].update(data=None)
                    self.remove_car(values)
            elif event == "รายละเอียดรถ":
                if (values["license_plate"] == ""):
                    sg.popup("กรุณากรอกเลขทะเบียน")
                else:
                    license_plate = values["license_plate"]
                    if license_plate in self.parking_lot.cars:
                        filePath = self.parking_lot.cars[license_plate]['filePath']
                        if (filePath != ""):
                            self.window['-IMAGE-'].update(data=convert_to_bytes(filePath, resize=(300, 300)))
                        else:
                            self.window['-IMAGE-'].update(data=None)
                        self.window['-license_plate-'].update(license_plate)
                        self.window["รถออก"].update(visible=True)
                    else:
                        sg.popup("ไม่พบเลขทะเบียนในระบบ")
            elif event == "table":
                for i in range(len(values["table"])):
                    print(values["table"][i])
            elif event == "Graph":
                self.window2 = self.make_win2()
                self.draw_bar_chart(self.parking_lot.carsOut)
            elif event == "ประวัติรถเข้า-ออก":
                if self.parking_lot.cars or self.parking_lot.carsOut:
                    self.draw_parking_history()
                else:
                    sg.popup("ไม่มีข้อมูลรถเข้า-ออกในระบบ")
            elif event == "Next":
                if self.current_page < self.get_max_page() - 1:
                    self.current_page += 1
                    self.draw_bar_chart(self.parking_lot.carsOut)
                else:
                    sg.popup("ไม่มีหน้าถัดไปแล้ว")
            elif event == "Previous":
                if self.current_page > 0:
                    self.current_page -= 1
                    self.draw_bar_chart(self.parking_lot.carsOut)
                else:
                    sg.popup("นี้คือหน้าแรกแล้ว")


            self.parking_lot.update_remaining_and_overtime()
            self.update_table()

        self.window.close()

    def add_car(self, values):
        license_plate = values["license_plate"]
        hours = int(values["hours"])
        minutes = int(values["minutes"])
        seconds = int(values["seconds"])
        filePath = values["filePath"]
        self.window["filePath"].update("")
        self.window["license_plate"].update("")
        self.parking_lot.add_car(license_plate, hours, minutes, seconds, filePath)

    def remove_car(self, values):
        license_plate = values["license_plate"]
        self.parking_lot.addToCarOut(license_plate,
                                     self.parking_lot.cars[license_plate]['expiration_time'],
                                     self.parking_lot.cars[license_plate]['remaining_time'],
                                     self.parking_lot.cars[license_plate]['overtime'],
                                     self.parking_lot.cars[license_plate]['filePath'])
        self.parking_lot.remove_car(license_plate)

    def get_max_page(self):
        total_items = len(self.parking_lot.carsOut)
        max_page = total_items // self.items_per_page
        if total_items % self.items_per_page != 0:
            max_page += 1
        return max_page

    def scan_license_plate(self, values):
        url = "https://api.aiforthai.in.th/lpr-v2"
        headers = {
            'Apikey': "jKpxZgIPGAsKBIOkuzoDVTl1J9wRtH8W"
        }
        payload = {'crop': '1', 'rotate': '1'}
        files = {'image': (values["filePath"], open(values["filePath"], 'rb'))}
        response = requests.post(url, files=files, data=payload, headers=headers)

        if response.text:
            print(response.json())
            data = response.json()
            license_plate = data[0]['lpr']
            self.window["license_plate"].update(license_plate)
            print("found license plate:", license_plate)

        else:
            sg.popup("ไม่พบเลขทะเบียน")

    def update_table(self):
        data = []
        for car in self.parking_lot.get_parked_cars():
            remaining_time = self.parking_lot.cars[car]['remaining_time']
            formatted_remaining_time = self.parking_lot.format_remaining_time(remaining_time)
            overtime = self.parking_lot.cars[car]['overtime']
            formatted_overtime = self.parking_lot.format_remaining_time(overtime)
            data.append([car, formatted_remaining_time, formatted_overtime])

        self.window["table"].update(values=data)

    def draw_parking_history(self):
        self.parking_history = self.parking_lot.get_parked_history()

        layout = [
            [sg.Text('ประวัติรถเข้า-ออก', font=("Helvetica", 20))],
            [sg.Table(values=self.parking_history, headings=["ทะเบียนรถ", "เวลาที่เหลือ", "เวลาที่เกิน"],
                      auto_size_columns=False, justification='center', num_rows=min(25, len(self.parking_history)))]
        ]
        self.history_window = sg.Window('ประวัติรถเข้า-ออก', layout, finalize=True)

        while True:
            window, event, values = sg.read_all_windows()
            #print(f"Event: {window} : {event}")
            if event == sg.WIN_CLOSED:
                print("history window closed")
                self.history_window.close()
                break

    def draw_bar_chart(self, cars_out, isShowRemainingTime=True, isShowOvertime=True):
        # Calculate start and end indices for the items on the current page
        start_index = self.current_page * self.items_per_page
        end_index = start_index + self.items_per_page

        # Get only the items for the current page
        cars_out_page = dict(list(cars_out.items())[start_index:end_index])

        graph: sg.Graph = self.window2['-GRAPH-']
        graph.erase()
        cars_out_keys = list(cars_out_page.keys())

        img = Image.new('RGB', (200, 50), color=(170, 182, 211))
        d = ImageDraw.Draw(img)
        fnt = ImageFont.truetype('./Font/arial.ttf', 12)
        d.text((10, 10), "Remaining time", font=fnt, fill=(0, 255, 0))
        d.text((10, 30), "Overtime", font=fnt, fill=(255, 0, 0))
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        graph.draw_image(data=bio.getvalue(), location=(GRAPH_SIZE[0] // 2 - 100, GRAPH_SIZE[1] // 2 - 50))

        # Define a constant for the right shift
        RIGHT_SHIFT = 20

        # Draw y-axis line
        graph.draw_line((EDGE_OFFSET + (RIGHT_SHIFT/2)-5, (-GRAPH_SIZE[0] // 2)-5),
                        (EDGE_OFFSET + (RIGHT_SHIFT/2)-5, (GRAPH_SIZE[1] // 2)))

        SPACING_FACTOR = 1.0  # adjust this value to increase or decrease the space between labels
        for i in range(25):  # 24 hours plus 0
            if(i % 2 == 0):
                y = GRAPH_SIZE[1] // 2 - i * (GRAPH_SIZE[1] // 2) / 24 * SPACING_FACTOR
                graph.draw_text(str(i), (EDGE_OFFSET + RIGHT_SHIFT - 20, -y), color='black')
                graph.draw_line((EDGE_OFFSET + RIGHT_SHIFT - 16, -y), (EDGE_OFFSET + RIGHT_SHIFT -13, -y))


        for i, car in enumerate(cars_out_page.values()):
            try:
                total_seconds = int(car["remaining_time"].total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                h, m, s = map(int, f"{hours}:{minutes}:{seconds}".split(":"))
                remaining_time_in_seconds = (h * 3600 + m * 60 + s) / (24 * 3600) * GRAPH_SIZE[1] // 2

                total_seconds = int(car["overtime"].total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                h, m, s = map(int, f"{hours}:{minutes}:{seconds}".split(":"))
                overtime_in_seconds = (h * 3600 + m * 60 + s) / (24 * 3600) * GRAPH_SIZE[1] // 2
            except:
                h, m, s = map(int, str(car["remaining_time"]).split(":"))
                remaining_time_in_seconds = (h * 3600 + m * 60 + s) / (24 * 3600) * GRAPH_SIZE[1] // 2

                h, m, s = map(int, str(car["overtime"]).split(":"))
                overtime_in_seconds = (h * 3600 + m * 60 + s) / (24 * 3600) * GRAPH_SIZE[1] // 2


            if(isShowRemainingTime):
                graph.draw_rectangle(top_left=(i * BAR_SPACING + EDGE_OFFSET + RIGHT_SHIFT, -GRAPH_SIZE[0] // 2),
                                 bottom_right=(i * BAR_SPACING + EDGE_OFFSET + BAR_WIDTH,
                                               -GRAPH_SIZE[0] // 2 + remaining_time_in_seconds),
                                 fill_color='green')
            if(isShowOvertime):
                if(not isShowRemainingTime):

                    graph.draw_rectangle(
                        top_left=(i * BAR_SPACING + EDGE_OFFSET + RIGHT_SHIFT, -GRAPH_SIZE[0] // 2 ),
                        bottom_right=(i * BAR_SPACING + EDGE_OFFSET + BAR_WIDTH,
                                      -GRAPH_SIZE[0] // 2  + overtime_in_seconds),
                        fill_color='red')
                else:
                    graph.draw_rectangle(
                        top_left=(i * BAR_SPACING + EDGE_OFFSET + RIGHT_SHIFT, -GRAPH_SIZE[0] // 2 + remaining_time_in_seconds),
                        bottom_right=(i * BAR_SPACING + EDGE_OFFSET + BAR_WIDTH,
                                      -GRAPH_SIZE[0] // 2 + remaining_time_in_seconds + overtime_in_seconds),
                        fill_color='red')


            img = Image.new('RGB', (100, 30), color=(170, 182, 211, 0))
            d = ImageDraw.Draw(img)
            fnt = ImageFont.truetype('./Font/RSU_BOLD.ttf', 16)
            d.text((40, 0), cars_out_keys[i], font=fnt, fill=(0, 0, 0))
            img = img.rotate(90, expand=1)
            bio = io.BytesIO()
            img.save(bio, format='PNG')
            graph.draw_image(data=bio.getvalue(), location=(i * BAR_SPACING + EDGE_OFFSET + RIGHT_SHIFT/2 , -GRAPH_SIZE[0] // 2))

