# Simple System for Automated Trading on bitFlyer

## Overview
This is a simple system for automated trading on Bitflyer. The system uses exponential moving average (EMA) for trading. This is a practice project and is NOT intended to run on other people's devices.

## Description
### Environment
| -------------- | -------------- |
|  Trading Floor |  bitFlyer  |
| Device | Raspberry Pi 4B <br> 4GB model  |
|  OS  |  Raspberry Pi OS  |
|  Language | Python 3.9.7 |

### Trading Algorithm
#### Trade Timing
To determine when to buy and sell, this system uses the exponential moving average (EMA). The system checks the EMA once every hour and takes a long position if the EMA5 and EMA20 form a golden cross. If the EMA5 and EMA20 form a dead cross, the system closes the position.
To simplify the algorithm, this system takes up to one position at the same time. Hence, when purchasing a currency, it uses all the Japanese yen held to purchase it. Moreover, the system doesn't take a short position. 
#### Preparing for a Crash
In addition to checking the EMA once an hour, it always checks the valuation of the currency it is holding. If the value of the currency is below 90% of the original purchase price, the position is closed.

### LINE Notification
When the system takes a position or closes a position, the line is notified. The notification will show the execution time, side, execution price, and the volume of cryptocurrency traded. If a position is closed, the profit (or loss) made by the position will be displayed in addition to them.