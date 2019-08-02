# VPT
Varna Public Transport custom component for Home Assistant

This custom component holds data for city of Varna, Bulgaria public transport card. 
The information for bus stop is scraped from https://varnatraffic.com website 

You can find the card at [https://github.com/Serios/VPT-Card](https://github.com/Serios/VPT-Card).

### Installation
Download the files from custom_components/varna_public_transport into your 
$homeassistant_config_dir/custom_components/varna_public_transport

Once downloaded and configured as per below information you'll need to restart HomeAssistant to have the custom component and the sensors platform loaded.

### Configuration

Define the sensor in your yaml file with the following configuration parameters:

| Name | Type |         | Default | Description |
|------|------|---------|---------|-------------|
| platform | string | **required** | `varna_public_transport` |  |
| stopId | string | **required** |  | This is the bus stop id. See [How to get bus stop id](#getting-bus-stop-id) |
| stopName | string | optional |  | What is the name of the stop. This will be shown as card title |
| show_mode | string | optional | all | What data to be scraped/shown in the card. See [Showing information](#showing-different-types-of-information) |
| max_schedule | int | optional | 10 | Numer of shedules times to be returned. Used in Schedules information. See [Showing information](#showing-different-types-of-information) |
| interval | int | optional | 30 | How offten the sensor shoud scrape for data (in seconds). Note: It is not advisible to put value bellow 10 |
| monitored_lines | list | optional |  | Which lines, comming trough the bus stop, you want to track. See [Showing information](#showing-different-types-of-information) |

Example of basic config

```yaml
- platform: varna_public_transport
  stopId: '553'
  stopName: 'Historical Museum'
```

![VPT-Card Lovelace example](https://github.com/Serios/VPT-Card/blob/master/vpt_card_preview.jpg)

###Showing different types of information
By defalut the sensor will return all data scraped for the bus stop. This include:
* live data - lines comming to the bus stop at this moment provided by vehicle tracker device. See bellow what kind of information this data contains.
* schedules - Schedule times for diffrent lines comming to the stop. See bellow what kind of information this data contains.

By setting `show_mode` property you can control what data is scraped/returned. Available options are:
`all` - returns both live data and schedules
`live` - returns only live data 
`schedule` - returns only schedule times

#### Live data
This contains:
Vehicle type - Bus or Trolley 
Line number 
Next schedule time - at which the vehicle should be on the stop
Vehicle delay - from the schedule time at which ariving to the stop
Vehicle extras - like airconditioning, wheelcheer access, etc.
Minutes left = before vehicle arrival at the stop based on the delay from schedule,
Distance of the vehicle - distance left to the bus stop.

Showing live data will use `interval` option to scrape https://varnatraffic.com website each N seconds for data

#### Schedule times
This contains:
Line number 
Next schedule times - The times (ahead from last scrape) at which the vehicles on this lines should be on the stop.

Showing `schedule` only don't use `interval` option. Instead the data is scraped on predefined time intervals based on `max_schedule` option value. Thus reducing request to https://varnatraffic.com website to only a couple a day

#### Limiting the number of lines for wich information is returned (both Live and Schedule)
By default the sensor will return data for all the lines that are comming to the bus stop. If you don't want that, and need only data for some lines, to be returned, you can specify the line numbers.
The syntax is simple:

```yaml
  monitored_lines:
    - 41
    - 148
```
Important!!!
There are some special line numbers for which https://varnatraffic.com website assign diffrent number than the actual one shown on the bus and use some internal logic to track and show data. Bellow you will find the list with the line number and the actual line number you need to set, if you want to track this line.
| Line number (shown on the bus) | Internal number (which you must set) |
|----|------|
| 17a | 117 |
| 18a | 1018 |
| 31a | 131 |
| 118a | 1118 |
| 209b | 219 |


#### Limiting the number of schedule times
Returning all times on which the vehicle should be on the stop trough the day is nonsence. This will overflow the sensor/card with data, thus by default this is set to 10 results. You can increase/decrease thi value by your likings.

###Some config examples

Basic config:
```yaml
- platform: varna_public_transport
  stopId: '553'
  stopName: 'Historical Museum'
```

Basic config with data scrape every 3 minutes (3 x 60 sec):
```yaml
- platform: varna_public_transport
  stopId: '553'
  stopName: 'Historical Museum'
  interval: 180
```

Show only live data:
```yaml
- platform: varna_public_transport
  stopId: '553'
  stopName: 'Historical Museum'
  show_mode: 'live'
```

Show only schedule data:
```yaml
- platform: varna_public_transport
  stopId: '553'
  stopName: 'Historical Museum'
  show_mode: 'schedule'
```

Show only schedule data and limit returned times by 5:
```yaml
- platform: varna_public_transport
  stopId: '553'
  stopName: 'Historical Museum'
  show_mode: 'schedule'
  max_schedule: 5
```

Show data only for lines 22, 41, 31a
```yaml
- platform: varna_public_transport
  stopId: '553'
  stopName: 'Historical Museum'
  monitored_lines:
    - 22
    - 41
    - 131
```