import os, time, yaml, requests, sys


with open("config.yaml") as f:
    config = yaml.load(f)


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
        r = requests.get(
            "https://api.telegram.org/bot%s/sendMessage" % self.token,
            params={
                "chat_id": config["telegram_chat_id"],
                "text": msg,
                "disable_notification": not notify,
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
        pass

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
            self.msg("error pinging %s" % addr, notify=True)

    def check_http(self, url, verify=True):
        try:
            hc = requests.get(url, timeout=config["http_checks_timeout"], verify=verify)
        except Exception as e:
            try:
                self.http_ok.remove(url)
            except KeyError:
                pass
            self.http_ko.add(url)
            self.msg("error reaching %s" % url, notify=True)
        else:
            self.http_ok.add(url)
            try:
                self.http_ko.remove(url)
            except KeyError:
                pass

    def report(self):
        msg = ("Ping errs/ok: %s/%s" "  HTTP errs/ok: %s/%s") % (
            len(self.ping_ko),
            len(self.ping_ok),
            len(self.http_ko),
            len(self.http_ok),
        )
        self.msg(msg, notify=(len(self.ping_ko) > 0 or len(self.http_ko) > 0))


mon = WitMon()
mon.msg("starting witmon", notify=False)

while True:
    try:
        for pc in config["ping_checks"]:
            mon.check_ping(pc)
    except TypeError:
        pass

    try:
        for hc in config["http_checks"]:
            mon.check_http(hc)
    except TypeError:
        pass

    try:
        for hc in config["http_checks_unsafe"]:
            mon.check_http(hc, verify=False)
    except TypeError:
        pass

    mon.report()
    time.sleep(300)
