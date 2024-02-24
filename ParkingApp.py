import requests
import PySimpleGUI as sg
import PIL.Image
import io
import base64

import ParkingLot

BAR_WIDTH = 10  # width of each bar
BAR_SPACING = 14  # space between each bar
EDGE_OFFSET = 3  # offset from the left edge for first bar
GRAPH_SIZE = (500, 500)  # size in pixels
def convert_to_bytes(file_or_bytes, resize=None):
    if isinstance(file_or_bytes, str):
        img = PIL.Image.open(file_or_bytes)
    else:
        try:
            img = PIL.Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))
        except Exception as e:
            dataBytesIO = io.BytesIO(file_or_bytes)
            img = PIL.Image.open(dataBytesIO)

    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height/cur_height, new_width/cur_width)
        img = img.resize((int(cur_width*scale), int(cur_height*scale)), PIL.Image.LANCZOS)
    with io.BytesIO() as bio:
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()

class ParkingApp:
    def __init__(self):
        self.window1 = self.make_win1()
        self.window2 = None
    def make_win1(self):
        sg.theme("LightBlue2")
        self.parking_lot = ParkingLot.ParkingLot()

        left_col = [[sg.Text("ระบบจอดรถ", font=("Helvetica", 20))],
                    [sg.Text("เลือกไฟล์รูปภาพ:"), sg.InputText(key="filePath", size=(42, 5)), sg.FileBrowse(),
                     sg.Button("สแกนทะเบียน")],
                    [sg.Text("เลขทะเบียน:"), sg.InputText(key="license_plate", size=(37, 5)), sg.Button("รถเข้าจอด"),
                     sg.Button("รายละเอียดรถ")],
                    [sg.Text("เวลา :"), sg.InputText(key="hours", size=(10, 5), default_text="0"), sg.Text("ชม"),
                     sg.InputText(key="minutes", size=(10, 5), default_text="0"), sg.Text("นาที"),
                     sg.InputText(key="seconds", size=(10, 5), default_text="0"), sg.Text("วินาที")],
                    [sg.Table(values=[], headings=["ทะเบียนรถ", "เวลาที่เหลือ", "เวลาเกิน"], key="table",
                              justification="center", auto_size_columns=False, col_widths=[20, 20, 20],
                              enable_events=True)],
                    [sg.Button("Graph"),sg.Button("ranCar"),sg.Button("ranCarOld")]]
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
                  [sg.Graph(GRAPH_SIZE, (0, -GRAPH_SIZE[0] // 2), (GRAPH_SIZE[0] // 2, GRAPH_SIZE[1] // 2),
                            k='-GRAPH-')],

                  [sg.Exit()]]
        return sg.Window('Bar Graph', layout, finalize=True)
    def run(self):
        while True:
            window, event, values = sg.read_all_windows(timeout=1000)
            # print(f"Event: {window} : {event}")
            if window == self.window and event == sg.WIN_CLOSED:
                print("window1 closed")
                break
            if window == self.window1 and event == "Graph":
                if self.window2 is None:
                    self.parking_lot.draw_bar_chart(self.parking_lot.carsOut)
                    self.window2 = self.make_win2()

            if window == self.window2 and event == sg.WIN_CLOSED:
                print("window2 closed")
                self.window2.close()
                self.window2 = None
            if window == self.window2 and event == "Exit":
                print("window2 closed")
                self.window2.close()
                self.window2 = None

            elif event == "สแกนทะเบียน":
                if(values["license_plate"] == ""):
                    if(values["filePath"] == ""):
                        sg.popup("กรุณาเลือกไฟล์รูปภาพ")
                    else:
                        self.scan_license_plate(values)

            elif event == "รถเข้าจอด":
                if(values["license_plate"] == ""):
                    sg.popup("กรุณากรอกเลขทะเบียน")
                else:
                    self.add_car(values)

            elif event == "รถออก":
                if(values["license_plate"] == ""):
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

            elif event == "ranCar":
                self.parking_lot.cars = self.parking_lot.generate_random_cars_out(5)
                print(self.parking_lot.cars)

            elif event == "ranCarOld":
                self.parking_lot.carsOut = self.parking_lot.generate_random_cars_out(5)
                print(self.parking_lot.carsOut)

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
        self.parking_lot.add_car(license_plate, hours, minutes, seconds,filePath)
    def remove_car(self, values):
        license_plate = values["license_plate"]
        self.parking_lot.addToCarOut(license_plate,
                                     self.parking_lot.cars[license_plate]['expiration_time'],
                                     self.parking_lot.cars[license_plate]['remaining_time'],
                                     self.parking_lot.cars[license_plate]['overtime'],
                                     self.parking_lot.cars[license_plate]['filePath'])
        self.parking_lot.remove_car(license_plate)
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
    def draw_bar_chart(self, cars_out):
        graph: sg.Graph = self.window2['-GRAPH-']
        graph.erase()

        for i, car in enumerate(cars_out.values()):
            try:
                total_seconds = int(car["remaining_time"].total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                h, m, s = map(int, f"{hours}:{minutes}:{seconds}".split(":"))
                remaining_time_in_seconds = (h * 3600 + m * 60 + s) / 250

                total_seconds = int(car["overtime"].total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                h, m, s = map(int, f"{hours}:{minutes}:{seconds}".split(":"))
                overtime_in_seconds = (h * 3600 + m * 60 + s) / 250
            except:
                h, m, s = map(int, str(car["remaining_time"]).split(":"))
                remaining_time_in_seconds = (h * 3600 + m * 60 + s) / 250

                h, m, s = map(int, str(car["overtime"]).split(":"))
                overtime_in_seconds = (h * 3600 + m * 60 + s) / 250



            graph.draw_rectangle(top_left=(i * BAR_SPACING + EDGE_OFFSET, -GRAPH_SIZE[0] // 2),
                                 bottom_right=(i * BAR_SPACING + EDGE_OFFSET + BAR_WIDTH,
                                               -GRAPH_SIZE[0] // 2 + remaining_time_in_seconds),
                                 fill_color='green')

            graph.draw_rectangle(
                top_left=(i * BAR_SPACING + EDGE_OFFSET, -GRAPH_SIZE[0] // 2 + remaining_time_in_seconds),
                bottom_right=(i * BAR_SPACING + EDGE_OFFSET + BAR_WIDTH,
                              -GRAPH_SIZE[0] // 2 + remaining_time_in_seconds + overtime_in_seconds),
                fill_color='red')