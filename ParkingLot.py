from datetime import datetime, timedelta
import random

class ParkingLot:
    def __init__(self):
        self.cars = {}
        self.carsOut = {}
    def add_car(self, license_plate, hours, minutes, seconds,filePath):
        now = datetime.now()
        expiration_time = now + timedelta(hours=hours, minutes=minutes, seconds=seconds)
        self.cars[license_plate] = {
            'expiration_time': expiration_time,
            'remaining_time': expiration_time - now,
            'overtime': timedelta(0),
            'filePath': filePath
        }
        print(self.cars)
    def editExpiration_time(self, license_plate, hours, minutes, seconds):
        now = datetime.now()
        expiration_time = now + timedelta(hours=hours, minutes=minutes, seconds=seconds)
        self.cars[license_plate]['expiration_time'] = expiration_time
        self.cars[license_plate]['remaining_time'] = expiration_time - now
    def remove_car(self, license_plate):
        self.cars.pop(license_plate)
    def addToCarOut(self,license_plate,expiration_time,remaining_time,overtime,filePath):
        self.carsOut[license_plate] = {
            'expiration_time': expiration_time,
            'remaining_time': remaining_time,
            'overtime': overtime,
            'filePath': filePath
        }
    def update_remaining_and_overtime(self):
        now = datetime.now()
        for car in self.cars:
            remaining_time = self.cars[car]['expiration_time'] - now
            if remaining_time.total_seconds() < 0:
                self.cars[car]['remaining_time'] = timedelta(0)
                self.cars[car]['overtime'] = now - self.cars[car]['expiration_time']
            else:
                self.cars[car]['remaining_time'] = remaining_time
                self.cars[car]['overtime'] = timedelta(0)


    def get_parked_cars(self):
        return list(self.cars.keys())
    def get_parked_history(self):
        parking_history = []
        for car in self.carsOut:
            remaining_time = self.carsOut[car]['remaining_time']
            overtime = self.carsOut[car]['overtime']
            parking_history.append([car, remaining_time, overtime])
        return parking_history
    def format_remaining_time(self, remaining_time):
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return "{:02}:{:02}:{:02}".format(hours, minutes, seconds)
    def generate_random_license_plate(self):
        # Function to generate a random license plate
        letters = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(2))
        numbers = ''.join(random.choice('0123456789') for _ in range(4))
        return f"{letters}{numbers}"
    def generate_random_duration(self):
        # Function to generate a random duration in hours, minutes, and seconds
        hours = random.randint(0, 10)
        minutes = random.randint(0, 59)
        seconds = random.randint(0, 59)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    def generate_random_cars_out(self, num_cars):
        # Function to generate random carsOut data
        car = {}
        for i in range(1, num_cars + 1):
            hours, minutes, seconds = map(int, self.generate_random_duration().split(":"))
            expiration_time = datetime.now() + timedelta(hours=hours, minutes=minutes, seconds=seconds)
            license_plate = self.generate_random_license_plate()
            remaining_time = self.generate_random_duration()
            overtime = self.generate_random_duration()

            car_data = {
                "expiration_time": expiration_time,
                "remaining_time": remaining_time,
                "overtime": overtime
            }
            car[license_plate] = car_data

        self.carsOut.update(car)