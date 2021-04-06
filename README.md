# Roll-API

**R**andom
**O**perator with
**L**arge
**L**atency

## The problem

TODO

## Solution

TODO

### Building

The actual machine that rolls the dice is called RollER - Roll **E**xecution **R**untime

TODO

### Backend

Current Roll-API backend that runs everything together looks like this:

- Python Flask that's serving the API and scheduling jobs to RQ
- RQ worker that shakes the dice and takes pictures of it
- RQ worker that analyzes pictures and counts how many dots are on the dice
- Redis, for RQ
- preferably, a reverse proxy - in my case, that's Caddy

#### Installation

Currently, there are no fancy Docker containers, or even pip venv - if you want to be super clean and isolate
everything, but since I'm running this on a single Raspberry Pi Zero W, that can't take anything more anyway, I just
install everything globally

0. Get yourself a Raspberry Pi with a camera, and install RpiOS on it - can be Light version - as
   always, `sudo apt update && sudo apt upgrade`
1. Git clone this, obviously: `git clone https://github.com/TheLastGimbus/Roll-API`
2. Install pip dependencies: `pip3 install -r requirements.txt`
3. Install Redis: `sudo apt install redis-server`
4. Do yourself a favor, ignore all online tutorials, grab a cup of coffee and `sudo apt install python3-opencv`

Great! If I didn't forget anything above, you should have everything required to run!

#### Running

TODO
