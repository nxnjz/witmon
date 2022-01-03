import os, time, yaml, requests, sys
from datetime import datetime

from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

with open("config.yaml") as f:
    config = yaml.load(f, Loader=Loader)


class Telegram:
    def __init__(self, token):
        self.token = token
        if len(sys.argv) > 1 and sys.argv[1] == "init":
            updates = requests.get(
                "https://api.telegram.org/bot%s/getUpdates" % self.token,
            ).json()
            # to manually get chat_id so the bot can message me
            # should add the bot or send it a message before to create an update.
            print(updates)

    def msg(self, msg, notify=True):
        for cid in config["telegram_chat_ids"]:
            r = requests.get(
                "https://api.telegram.org/bot%s/sendMessage" % self.token,
                params={
                    "chat_id": cid,
                    "text": msg,
                    "disable_notification": not notify,
                    "parse_mode": "MarkdownV2",
                },
            )
            print(r.text)


tg = Telegram(config["telegram_bot_access_token"])


class WitMon:
    def __init__(self):
        self.ping_ok = set()
        self.ping_ko = set()
        self.http_ok = set()
        self.http_ko = set()
        self.last_report = datetime.now()
        self.was_degraded = True

    def msg(self, msg, notify):
        tg.msg(msg, notify)

    def check_ping(self, addr):
        ec = os.system("ping -c 1 %s" % addr)
        if ec == 0:
            self.ping_ok.add(addr)
            try:
                self.ping_ko.remove(addr)
            except KeyError:
                pass
        else:
            try:
                self.ping_ok.remove(addr)
            except KeyError:
                pass
            self.ping_ko.add(addr)
            self.msg("ERROR pinging %s" % addr, notify=True)

    def check_http(self, url, verify=True):
        try:
            hc = requests.get(url, timeout=config["http_checks_timeout"], verify=verify)
        except Exception as e:
            try:
                self.http_ok.remove(url)
            except KeyError:
                pass
            self.http_ko.add(url)
            self.msg("ERROR reaching %s" % url, notify=True)
        else:
            self.http_ok.add(url)
            try:
                self.http_ko.remove(url)
            except KeyError:
                pass

    def is_degraded(self):
        return len(self.ping_ko) > 0 or len(self.http_ko) > 0

    def report(self):
        if (
            self.is_degraded()
            or self.was_degraded
            or (datetime.now() - self.last_report).total_seconds()
            > config["healthy_report_interval"]
        ):
            msg = ("*%s* \n\nPing errs/ok: %s/%s" "  \nHTTP errs/ok: %s/%s") % (
                "DEGRADED" if self.is_degraded() else "HEALTHY",
                len(self.ping_ko),
                len(self.ping_ok),
                len(self.http_ko),
                len(self.http_ok),
            )
            self.msg(msg, notify=self.is_degraded())
            self.last_report = datetime.now()
        self.was_degraded = self.is_degraded()


mon = WitMon()
mon.msg("starting witmon", notify=False)

while True:
    try:
        for pc in config["ping_checks"]:
            mon.check_ping(pc)
    except TypeError:
        print("ping_checks is not a list, ignoring", file=sys.stderr)
        pass

    try:
        for hc in config["http_checks"]:
            mon.check_http(hc)
    except TypeError:
        print("http_checks is not a list, ignoring", file=sys.stderr)
        pass

    try:
        for hc in config["http_checks_unsafe"]:
            mon.check_http(hc, verify=False)
    except TypeError:
        print("http_checks_unsafe is not a list, ignoring", file=sys.stderr)
        pass

    mon.report()
    time.sleep(config["checks_interval"])
