#!/usr/bin/env python3
"""Monitor a tool and turn on a fan."""
from time import sleep

import click
from logzero import logger
import pigpio

DEFAULT_TOOL_PIN: int = 8

DEFAULT_FAN_PIN: int = 12
FAN_MAX_DUTY_CYCLE: int = 99 * 10_000

DEFAULT_FAN_SPEED: int = 50


class Fan:
    """Manage the Fume Hood's Fan.

    Args:
        fan_pin: The PWM signal pin of tha fan
        pi: The GPIO instance ``fan_pin`` can be accessed from
        fan_speed: The speed at which the fan should run (0-100) when the tool is removed

    """

    def __init__(self, fan_pin: int, pi: pigpio.pi, fan_speed: int = DEFAULT_FAN_SPEED):
        self._pi = pi
        self.pin = fan_pin
        self.fan_speed = fan_speed

        self._pi.set_mode(self.pin, pigpio.OUTPUT)
        logger.info('Controlling fan on pin %d', self.pin)
        logger.info('Fan speed: %d', self.fan_speed)
        self.off()

    def set_speed(self, value: int):
        """Set the speed of the fan as an interger percent (0-100).

        Args:
            value: The speed for the fan.

        """
        if value != 0:
            value = int((1-(value / 100)) * FAN_MAX_DUTY_CYCLE)
        else:
            value = FAN_MAX_DUTY_CYCLE
        self._pi.hardware_PWM(
            self.pin,
            25_000,
            PWMduty=value,
        )

    def on(self):
        """Turn the fan on at the speed specified by ``self.fan_speed``"""
        self.set_speed(self.fan_speed)

    def off(self):
        """Turn off the fan."""
        self.set_speed(0)


class Tool:
    """Monitor te soldering iron on its dock.
    
    Args:
        tool_pin: The pin for the soldering iron
        pi: The GPIO instance ``tool_pin`` can be accessed from
        fan: The fan to toggle via `Tool` presence

    """

    def __init__(self, tool_pin: int, pi: pigpio.pi, fan: Fan):
        self.pin = tool_pin
        self.tool_active = False
        self._pi = pi
        self._pi.set_mode(self.pin, pigpio.INPUT)
        self._pi.set_pull_up_down(self.pin, pigpio.PUD_DOWN)
        logger.info('Monitoring tool on pin %d', tool_pin)
        self.fan = fan


    def remove_tool(self):
        """Remove the tool and turn on the fan."""
        if not self.tool_active:
            print('Tool removed')
            self.tool_active = True
            self.fan.on()

    def replace_tool(self):
        """Tool has been replaced, turn off the fan."""
        if self.tool_active:
            print('Tool replaced')
            self.fan.off()
            self.tool_active = False

    def monitor(self):
        """Monitor the tool pin and dispatch based on tool presence."""
        try:
            while True:
                if self._pi.read(self.pin):
                    self.remove_tool()
                else:
                    self.replace_tool()
                sleep(1)
        except KeyboardInterrupt:
            logger.info('Keyboard Interrupt caught. Returning control')

@click.command()
@click.option('--tool-pin', '-t', help='The pin to which the tool is connected', default=DEFAULT_TOOL_PIN, type=int)
@click.option('--fan-pin', '-f', help='The pin to which the fan is connected', default=DEFAULT_FAN_PIN, type=int)
@click.option('--fan-speed', '-s', help='The integer percent (0-100) speed the fan should spin at.', default=DEFAULT_FAN_SPEED, type=int)
def fume_hood(tool_pin: int, fan_pin: int, fan_speed: int):
    pi = pigpio.pi()
    Tool(
        tool_pin=tool_pin,
        pi=pi,
        fan=Fan(
            fan_pin=fan_pin, 
            pi=pi,
            fan_speed=fan_speed,
        ),
    ).monitor()

if __name__ == '__main__':
    fume_hood()
