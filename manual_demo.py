"""Interactive, sensorless demonstration; dry-run unless --hue is explicit."""
import argparse
import threading

from hub import Hub
from talkback import COMMANDS, from_environment, poll_loop
from webapp import run_controller


def command(hub, text):
    if text in COMMANDS:
        hub.manual(text.lower())
    elif text in ('SCREEN DOWN', 'SCREEN UP'):
        # Explicitly simulated contact, never represented as a real sensor reading.
        with hub.lock:
            hub.policy.screen_down = text == 'SCREEN DOWN'
            if hub.policy.screen_down:
                hub.override = None
    else:
        raise ValueError('Bruk WHITE, WARM, CINEMA, OFF, AUTO, SCREEN DOWN/UP eller QUIT')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hue', action='store_true', help='Send actual Hue requests')
    parser.add_argument('--talkback', action='store_true')
    args = parser.parse_args()
    hub = Hub(demo=not args.hue, manual_only=True)
    if args.hue:
        from settings import required
        required('HUE_BRIDGE_HOST')
        required('HUE_USERNAME')
    consumer = from_environment(hub) if args.talkback else None
    stop = threading.Event()
    workers = [threading.Thread(target=run_controller, args=(hub, stop), daemon=True)]
    if consumer:
        workers.append(threading.Thread(target=poll_loop, args=(consumer, stop), daemon=True))
    for worker in workers:
        worker.start()
    print('EKTE HUE' if args.hue else 'TØRRKJØRING: ingen nettverkskall til Hue')
    print('Ingen sensorer. SCREEN DOWN/UP simulerer lerret. AUTO/utløp beholder siste lys.')
    try:
        while True:
            text = input('Kommando> ').strip().upper()
            if text == 'QUIT':
                break
            try:
                command(hub, text)
                print(hub.desired())
            except ValueError as error:
                print(error)
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        stop.set()
        for worker in workers:
            worker.join(timeout=6)


if __name__ == '__main__':
    main()
