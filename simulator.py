import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


class Simulation:
    def __init__(self, time_factor, total_duration, car):
        self.time = 1
        self.time_factor = time_factor  # how many subdivisions of an hour there should be
        self.duration = total_duration
        self.car = car

    def start(self):
        print("\t\t--- Start of Simulation ---")
        print(self.car.status_text(self.duration))

        while not self.is_done():
            self.tick()
        print("\t\t--- End of Simulation ---")
        print(self.car.status_text(self.duration))
        self.car.plot()

    def is_done(self):
        return self.time > self.duration

    def tick(self):
        self.car.tick(self.time, self.duration)
        self.time += 1


class Car:
    def __init__(self, time_factor, charge_speed_per_hour=21000, distance_per_hour=70):
        self.time_factor = time_factor
        self.charging = False
        self.battery_capacity = 70000
        self.battery_charge = self.battery_capacity
        self.battery_charge_total = self.battery_charge
        self.energy_usage_per_tick = power_for_velocity(distance_per_hour / 3.6) * self.time_factor
        self.charge_speed_per_tick = charge_speed_per_hour * self.time_factor
        self.number_of_charging_stops = 0
        self.distance_driven = 0
        self.distance_per_tick = distance_per_hour * self.time_factor
        self.charge_level_history = []
        self.distance_driven_history = []
        self.time_history = []

    def tick(self, time, total_duration):
        if self.charging or (self.battery_charge - self.energy_usage_per_tick) <= 0:
            self.charge(time, total_duration)
        else:
            self.drive()

        self.time_history.append(time)
        self.charge_level_history.append(self.battery_charge)
        self.distance_driven_history.append(self.distance_driven)

    def drive(self):
        self.battery_charge -= self.energy_usage_per_tick
        self.distance_driven += self.distance_per_tick

    def charge(self, time, total_duration):
        if not self.charging:
            self.charging = True
            self.number_of_charging_stops += 1

        self.battery_charge += self.charge_speed_per_tick
        self.battery_charge_total += self.charge_speed_per_tick

        if self.is_fully_charged() or self.is_sufficiently_charged(time, total_duration):
            self.charging = False

    def is_fully_charged(self):
        return (self.battery_charge + self.charge_speed_per_tick) > self.battery_capacity

    def is_sufficiently_charged(self, time, total_duration):
        remaining_time = total_duration - time
        return self.battery_charge > (remaining_time * self.energy_usage_per_tick)

    def plot(self):
        fig, axe_distance = plt.subplots()
        axe_distance.plot(self.time_history, self.distance_driven_history, label='Distance')
        axe_distance.set_ylabel("Distance (km)")
        axe_distance.set_xlabel("Time (hours)")
        axe_distance.set_title(f"EV Endurance Tactics - Target Speed: {self.distance_per_tick / self.time_factor:.0f} km/h")
        axe_distance.legend(loc='lower left')
        axe_distance.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: round(x * self.time_factor, 1)))

        axe_charge = axe_distance.twinx()
        axe_charge.plot(self.time_history, self.charge_level_history, label='Charge Level', color='red')
        axe_charge.set_ylabel("Charge Level (kWh)")
        axe_charge.legend(loc='upper left')
        axe_charge.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: round(x / 1000)))
        fig.show()

    def status_text(self, duration):
        energy_per_km = (self.battery_charge_total - self.battery_charge) / self.distance_driven \
            if self.distance_driven else 0

        return f"""
        Battery Capacity (Wh): {self.battery_capacity}
        Battery Charge current (Wh): {self.battery_charge:.0f}
        Battery Charge total (Wh): {self.battery_charge_total:.0f}
        Battery Charge speed (W): {self.charge_speed_per_tick / self.time_factor:.0f}
        Number of charging stops: {self.number_of_charging_stops}
        Energy use per hour (Wh): {self.energy_usage_per_tick / self.time_factor:.0f}
        Energy use per tick (Wh): {self.energy_usage_per_tick:.1f}
        Energy use per km (Wh/km): {energy_per_km :.1f} 
        Distance per tick (km): {self.distance_per_tick:.4f}
        Distance driven (km): {self.distance_driven}
        Target speed (km/h): {self.distance_per_tick / self.time_factor:.4f}
        Average speed (km/h): {self.distance_driven / duration / self.time_factor}
        Time factor: {self.time_factor:.4f}
        Ticks per hour: {1 / self.time_factor:.1f}
        """


def power_for_velocity(velocity):
    # calculate air resistance
    roh = 1.2041
    coefficient_of_drag = 0.23
    area = 1.433 * 1.850  # from model 3 width * height
    cw_a = coefficient_of_drag * area
    force_air = cw_a * velocity * velocity / 2 * roh

    # calculate roll resistance
    c_r = 0.012  # asphalt 0.011-0,015 according Wikipedia.
    force_roll_resistance = c_r * 1950 * 9.81  # model 3 incl driver = 1,95t*g=F

    # vehicle has standby power, lets say 1kW. I think it was 500W in sentry mode only???
    power_standby = 1000

    # calculate power needed for specific velocity
    return (force_air + force_roll_resistance) * velocity + power_standby


if __name__ == '__main__':
    time_factor = 1 / 60
    total_duration = 24 / time_factor
    speeds = [70, 80, 85, 88, 90, 95, 100]

    for speed in speeds:
        simulation = Simulation(time_factor, total_duration, Car(time_factor, distance_per_hour=speed))
        simulation.start()
