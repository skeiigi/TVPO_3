"""Небольшое веб-приложение для демонстрации развёртывания на Linux."""

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from os import environ
from urllib.parse import parse_qs, urlparse

from mortgage import calculate


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.respond(200, "ok", "text/plain; charset=utf-8")
            return
        if parsed.path != "/":
            self.respond(404, "Страница не найдена", "text/plain; charset=utf-8")
            return

        params = parse_qs(parsed.query)
        values = {key: params.get(key, [default])[0] for key, default in
                  (("principal", "3000000"), ("annual_rate", "12"), ("years", "20"))}
        result = ""
        if parsed.query:
            try:
                data = calculate(**values)
                result = (f"<p>Ежемесячный платёж: <b>{data['monthly_payment']} ₽</b></p>"
                          f"<p>Всего выплат: {data['total_payment']} ₽</p>"
                          f"<p>Переплата: {data['overpayment']} ₽</p>")
            except ValueError as exc:
                result = f"<p class='error'>{escape(str(exc))}</p>"

        fields = "".join(
            f"<label>{label}<input name='{key}' type='number' step='{step}' "
            f"value='{escape(values[key], quote=True)}' required></label>"
            for key, label, step in (("principal", "Сумма кредита, ₽", "0.01"),
                                     ("annual_rate", "Ставка, % годовых", "0.01"),
                                     ("years", "Срок, лет", "any"))
        )
        page = f"""<!doctype html><html lang='ru'><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Ипотечный калькулятор</title>
<style>body{{font:18px system-ui;max-width:620px;margin:50px auto;padding:0 20px}}
label{{display:block;margin:16px 0}}input{{display:block;padding:10px;width:100%;box-sizing:border-box}}
button{{padding:10px 20px}}.error{{color:#b00020}}</style>
<h1>Ипотечный калькулятор</h1><form method='get'>{fields}<button>Рассчитать</button></form>
{result}</html>"""
        self.respond(200, page, "text/html; charset=utf-8")

    def respond(self, status, body, content_type):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", int(environ.get("PORT", "8000"))), Handler)
    server.serve_forever()
