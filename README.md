# Roll-API

**R**andom
**O**perator with
**L**arge
**L**atency

![API available badge](https://img.shields.io/website?down_color=red&label=API&up_color=green&url=https%3A%2F%2Froll.lastgimbus.com%2Fapi%2F)

This icon ↑ indicates if API is working right now 

## The problem :clown_face:

Today's cryptography is based on generating random numbers - or should I say, pseudo-random. Because computers can't
really do anything "randomly", they generate those numbers by passing them into algorithms back-and-forth.

THIS IS HIGHLY DANGEROUS! If the attacker got knowledge on what algorithm your code uses, they could reverse-guess what
numbers you generated, and thus, break your encryption!!!

## Solution :muscle:

If we want random numbers to protect us, we need those numbers to be **really** random - here comes Roll-API!
You make a request, and a special machine rolls a die, takes a picture of it, recognizes how many dots it has, and
returns the result!

![Roller working](images/roller_working.gif)

## How to use :monocle_face:

Whole API lives under [https://roll.lastgimbus.com/api/](https://roll.lastgimbus.com/api/)

(If you don't have `curl`, just paste those URLs into the browser)

(NOTE: All uuid's below are purely example - use your own, that you will get from `roll/`)

1. Make a request to [`roll/`](https://roll.lastgimbus.com/api/roll/):

   ```bash
   $ curl https://roll.lastgimbus.com/api/roll/
   7a1da923-0622-4848-b224-973f1b6c74f0
   ```
   It gives you a UUID of your request - you will use that to check if your roll is ready and what number was drawn
2. Make request to `info/<uuid>/` or `result/<uuid>/`:

   - `result/` gives you purely the result - this is useful when making some bash scripts :scroll:
      ```bash
      $ curl https://roll.lastgimbus.com/api/result/7a1da923-0622-4848-b224-973f1b6c74f0/
      6
      ```
      Response text, code:
       - \<number\>, 200 - here is your random number :tada:
       - "QUEUED", 202 - your request is waiting in the queue with other requests - it make take some time :hourglass:
       - "RUNNING", 201 - your request is being rolled right now - wait 5 seconds and it will be ready :fire:
       - "EXPIRED", 410 - your request has been sitting too long, and it's results don't exist anymore :confused: - make a
         new one :+1:
       - "FAILED", 500 - something failed inside the RollER - maybe dice was moving, idk :shrug: - make a new request and
         it should work :+1:

   - `info/` gives you a JSON with more info:
      ```bash
      $ curl https://roll.lastgimbus.com/api/info/7a1da923-0622-4848-b224-973f1b6c74f0/
      {
        # Estimated-time-arrival - estimated timestamp when result will be available
        "eta": 1618160853.0,
        # How many requests are before yours in queue
        "queue": 0,  
        # Your result - is null when not finished yet or expired
        "result": 6,  
        # Same statuses as with "result/", except it's "FINISHED" instead of a number
        "status": "FINISHED",  
        # Timestamp when results expire - "-1.0" when waiting in queue, "0.0" when expired or failed
        "ttl": 1618160343.0
      }
      ```
      (`info/` always returns a 200 :eyes:)

3. If you are curious how your dice looks - you can request the original image with `image/<uuid>/` :camera:

  ```bash
  $ curl https://roll.lastgimbus.com/api/image/7a1da923-0622-4848-b224-973f1b6c74f0/ > full-image.jpg
  $ ls
  full-image.jpg
  ```

   ![Example full image](images/example-full-image.jpg)

   You can also get image from CV analysis (in grayscale, cropped, and with marked detected dots) -
   at `anal-image/<uuid>/`:

  ```bash
  $ curl https://roll.lastgimbus.com/api/anal-image/7a1da923-0622-4848-b224-973f1b6c74f0/ > anal-image.jpg
  $ ls
  anal-image.jpg
  ```

   ![Example anal image](images/example-anal-image.jpg)

   If the request is not finished, it will return same responses as `result/`

### TTL - time to live :coffin:

Your results will be available for 5 minutes when finished. After that, you fill get "EXPIRED" messages, and you need to
make a new request.

## How to make :mechanic:

If you want to make something like this yourself, here is how

### Building :building_construction:

The actual machine that rolls the dice is called RollER - Roll **E**xecution **R**untime

TODO

### Backend :computer:

Current Roll-API backend that runs everything together looks like this:

- Python Flask that's serving the API and scheduling jobs to RQ
- RQ worker that shakes the dice and takes pictures of it
- RQ worker that analyzes pictures and counts how many dots are on the dice
- Redis, for RQ
- preferably, a reverse proxy - in my case, that's Caddy

#### Installation :cd:

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

#### Running :rocket:

TODO
